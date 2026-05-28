import { useEffect, useRef, useState, useCallback } from 'react';
import { proctoringService } from '../services/proctoring';

interface ProctoringConfig {
  assessmentAttemptId: string;
  onViolation?: (event: string) => void;
  onTerminated?: (reason: string) => void;
}

type ProctoringStatus =
  | 'idle'
  | 'waiting_permissions'
  | 'fullscreen_pending'
  | 'connecting_websocket'
  | 'ready'
  | 'failed'
  | 'terminated';

function withTimeout<T>(p: Promise<T>, ms: number, message: string) {
  return new Promise<T>((resolve, reject) => {
    const t = window.setTimeout(() => reject(new Error(message)), ms);
    p.then(
      (v) => {
        window.clearTimeout(t);
        resolve(v);
      },
      (e) => {
        window.clearTimeout(t);
        reject(e);
      },
    );
  });
}

export function useProctoring({ assessmentAttemptId, onViolation, onTerminated }: ProctoringConfig) {
  const [status, setStatus] = useState<ProctoringStatus>('idle');
  const [riskLevel, setRiskLevel] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('LOW');
  const [riskScore, setRiskScore] = useState(0);
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [isMicActive, setIsMicActive] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [stream, setStream] = useState<MediaStream | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const captureIntervalRef = useRef<number | null>(null);
  const streamingCleanupRef = useRef<(() => void) | null>(null);

  const wsInitTokenRef = useRef<{ url: string; token: string } | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const startedRef = useRef(false);
  const startPromiseRef = useRef<Promise<void> | null>(null);
  const unmountedRef = useRef(false);

  useEffect(() => {
    unmountedRef.current = false;
    return () => {
      unmountedRef.current = true;
    };
  }, []);

  const cleanup = useCallback(() => {
    if (captureIntervalRef.current) {
      window.clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }

    wsRef.current?.close();
    wsRef.current = null;

    if (streamingCleanupRef.current) {
      streamingCleanupRef.current();
      streamingCleanupRef.current = null;
    }

    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    } catch {
      // ignore
    }
    streamRef.current = null;
    setStream(null);
    setConnectionStatus('disconnected');

    try {
      mediaRecorderRef.current?.stop();
    } catch {
      // ignore
    }
    mediaRecorderRef.current = null;

    setIsWebcamActive(false);
    setIsMicActive(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendViolation = useCallback((type: string) => {
    // Try WebSocket first
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'violation',
          event_type: type,
          timestamp: new Date().toISOString(),
        }),
      );
      return;
    }
    // Fallback: send via REST API if we have a session
    if (sessionIdRef.current) {
      proctoringService.recordEvent({
        event_id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2),
        session_id: sessionIdRef.current,
        event_type: type,
        severity: type === 'TAB_SWITCH' || type === 'WINDOW_BLUR' ? 'MEDIUM' : 'HIGH',
        risk_score: type === 'TAB_SWITCH' ? 10 : type === 'WINDOW_BLUR' ? 5 : type === 'DEVTOOLS' ? 40 : type === 'RIGHT_CLICK' ? 10 : type === 'WINDOW_RESIZE' ? 15 : 10,
        timestamp: new Date().toISOString(),
        metadata: { details: `Frontend detected ${type}` }
      }).catch(() => {});
    }
  }, []);

  const attachBehaviorListeners = useCallback(() => {
    // ── Behavior Listeners (always attached regardless of camera/WS) ──
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        sendViolation('TAB_SWITCH');
      }
    };

    const handleBlur = () => {
      sendViolation('WINDOW_BLUR');
    };

    const handleCopy = () => {
      sendViolation('COPY');
    };

    const handlePaste = () => {
      sendViolation('PASTE');
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === 'F12' ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C'))
      ) {
        sendViolation('DEVTOOLS');
      }
    };

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      sendViolation('RIGHT_CLICK');
    };

    let lastWindowSize = { w: window.innerWidth, h: window.innerHeight };
    const handleResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      // Fire violation if window shrinks below 800x500 or drops by >40% from last size
      if (w < 800 || h < 500 || w < lastWindowSize.w * 0.6 || h < lastWindowSize.h * 0.6) {
        sendViolation('WINDOW_RESIZE');
      }
      lastWindowSize = { w, h };
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);
    document.addEventListener('copy', handleCopy);
    document.addEventListener('paste', handlePaste);
    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('contextmenu', handleContextMenu);
    window.addEventListener('resize', handleResize);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('paste', handlePaste);
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('contextmenu', handleContextMenu);
      window.removeEventListener('resize', handleResize);
    };
  }, [sendViolation]);

  const startStreaming = useCallback(() => {
    if (!wsRef.current || !streamRef.current) return;

    const videoTracks = streamRef.current.getVideoTracks();
    const audioTracks = streamRef.current.getAudioTracks();

    if (videoTracks.length === 0 && audioTracks.length === 0) return;

    // 1) Video streaming (every 1s)
    if (videoTracks[0] && (window as any).ImageCapture) {
      const imageCapture = new (window as any).ImageCapture(videoTracks[0]);
      captureIntervalRef.current = window.setInterval(async () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          try {
            const bitmap = await imageCapture.grabFrame();
            const canvas = document.createElement('canvas');
            canvas.width = 320;
            canvas.height = 240;
            const ctx = canvas.getContext('2d');
            ctx?.drawImage(bitmap, 0, 0, 320, 240);
            const base64Frame = canvas.toDataURL('image/jpeg', 0.6).split(',')[1];

            wsRef.current.send(JSON.stringify({ type: 'video', frame: base64Frame }));
          } catch (e) {
            console.error('Frame capture failed', e);
          }
        }
      }, 1000);
    }

    // 2) Audio streaming
    const mimeType = 'audio/webm';
    try {
      const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const result = reader.result as string;
            const base64Audio = result.split(',')[1];
            wsRef.current?.send(JSON.stringify({ type: 'audio', audio: base64Audio }));
          };
          reader.readAsDataURL(event.data);
        }
      };

      mediaRecorder.start(2000);
    } catch (e) {
      console.warn('Audio recorder init failed:', e);
    }

    // Return cleanup function to be called when session stops
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('paste', handlePaste);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [sendViolation]);

  const connectWS = useCallback(
    async (url: string, token: string) => {
      if (unmountedRef.current) return;

      setStatus('connecting_websocket');
      setConnectionStatus('connecting');
      const wsUrl = `${url}?token=${encodeURIComponent(token)}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      const openPromise = new Promise<void>((resolve, reject) => {
        const onOpen = () => {
          ws.removeEventListener('open', onOpen as any);
          resolve();
        };
        const onError = () => {
          reject(new Error('WebSocket error'));
        };
        ws.addEventListener('open', onOpen as any);
        ws.addEventListener('error', onError as any, { once: true });
      });

      ws.onopen = () => {
        if (unmountedRef.current) {
          ws.close();
          return;
        }
        setConnectionStatus('connected');
        // Always attach behavior listeners (tab switch, devtools, etc.)
        const cleanupListeners = attachBehaviorListeners();
        const cleanup_fn = startStreaming();
        streamingCleanupRef.current = () => {
          cleanupListeners?.();
          if (typeof cleanup_fn === 'function') cleanup_fn();
        };
        setStatus('ready');
      };

      ws.onmessage = (event) => {
        let data: any;
        try {
          data = JSON.parse(event.data);
        } catch {
          return;
        }

        if (data.type === 'risk_update') {
          setRiskScore(data.risk_score);
          setRiskLevel(data.risk_level);
        } else if (data.type === 'violation') {
          onViolation?.(data.event_type);
        } else if (data.type === 'termination') {
          setStatus('terminated');
          onTerminated?.(data.reason);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        if (streamingCleanupRef.current) {
          streamingCleanupRef.current();
          streamingCleanupRef.current = null;
        }
        if (!unmountedRef.current && startedRef.current && status !== 'terminated' && status !== 'failed') {
          const retry = wsInitTokenRef.current;
          if (retry) {
            window.setTimeout(() => {
              if (!unmountedRef.current) {
                connectWS(retry.url, retry.token).catch(() => {
                  if (!unmountedRef.current) setStatus('failed');
                });
              }
            }, 3000);
          }
        }
      };

      ws.onerror = () => {
        // handled by openPromise timeout/reject path
      };

      // timeout safety: if it never opens, fail fast
      try {
        await withTimeout(openPromise, 15000, 'WebSocket connection timed out');
      } catch {
        if (!unmountedRef.current) {
          cleanup();
          setStatus('failed');
        }
      }
    },
    [cleanup, onViolation, onTerminated, startStreaming, status],
  );

  const requestMediaPermissions = useCallback(async (): Promise<MediaStream> => {
    setStatus('waiting_permissions');
    const stream = await withTimeout(
      navigator.mediaDevices.getUserMedia({ video: true, audio: true }),
      20000,
      'Camera/mic permission timed out',
    );

    streamRef.current = stream;
    setStream(stream);
    setIsWebcamActive(stream.getVideoTracks().length > 0);
    setIsMicActive(stream.getAudioTracks().length > 0);
    return stream;
  }, []);

  const start = useCallback(async () => {
    // Guard: already started
    if (startedRef.current) {
      return startPromiseRef.current;
    }

    // Guard: no assessment ID
    if (!assessmentAttemptId) {
      setStatus('failed');
      return Promise.reject(new Error('No assessment attempt ID'));
    }

    startedRef.current = true;

    const promise = (async () => {
      try {
        // 1) Request fullscreen (soft fail)
        setStatus('fullscreen_pending');
        if (!document.fullscreenElement) {
          try { await document.documentElement.requestFullscreen(); }
          catch { console.warn('[Proctoring] Fullscreen not available'); }
        }

        // 2) Request webcam/mic permissions (soft fail)
        try { await requestMediaPermissions(); }
        catch { console.warn('[Proctoring] Camera/mic unavailable — violations still monitored'); }

        // 3) Initialize session via API
        setStatus('connecting_websocket');
        let sessionData: ProctoringSessionResponse | null = null;
        try {
          sessionData = await withTimeout(
            proctoringService.initializeSession(assessmentAttemptId),
            15000,
            'Session initialization timed out',
          );
        } catch {
          console.warn('[Proctoring] Session init failed — violations via REST fallback');
        }

        if (sessionData?.session_id) {
          sessionIdRef.current = sessionData.session_id;
          wsInitTokenRef.current = { url: sessionData.ws_url, token: sessionData.token };

          // 4) Connect WebSocket (soft fail)
          try { await connectWS(sessionData.ws_url, sessionData.token); }
          catch { console.warn('[Proctoring] WebSocket failed — violations via REST'); }
        }

        // 5) Always attach behavior listeners (independent of camera/WS)
        streamingCleanupRef.current = attachBehaviorListeners();
        setStatus('ready');
      } catch (err: any) {
        if (!unmountedRef.current) {
          cleanup();
          setStatus('failed');
        }
        startedRef.current = false;
        startPromiseRef.current = null;
        throw err;
      }
    })();

    startPromiseRef.current = promise;
    return promise;
  }, [assessmentAttemptId, cleanup, connectWS, requestMediaPermissions]);

  useEffect(() => {
    return () => {
      unmountedRef.current = true;
      cleanup();
    };
  }, [cleanup]);

  return {
    status,
    riskLevel,
    riskScore,
    isWebcamActive,
    isMicActive,
    connectionStatus,
    stream,
    start,
    sendViolation,
  };
}

import { useQuery } from '@tanstack/react-query';

export function useProctoringSession(assessmentId: string) {
  return useQuery({
    queryKey: ['proctoring-session', assessmentId],
    queryFn: async () => {
      const resp = await proctoringService.getSessionByAssessment(assessmentId);
      return resp.data || resp;
    },
    enabled: !!assessmentId,
  });
}

export function useProctoringEvents(sessionId: string) {
  return useQuery({
    queryKey: ['proctoring-events', sessionId],
    queryFn: async () => {
      const resp = await proctoringService.getEvents(sessionId);
      return (resp as any).data || resp;
    },
    enabled: !!sessionId,
  });
}

export function useProctoringEvidence(sessionId: string) {
  return useQuery({
    queryKey: ['proctoring-evidence', sessionId],
    queryFn: async () => {
      const resp = await proctoringService.getEvidence(sessionId);
      return (resp as any).data || resp;
    },
    enabled: !!sessionId,
  });
}
