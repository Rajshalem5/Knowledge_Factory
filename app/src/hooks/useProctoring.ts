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
  const sessionIdRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const captureIntervalRef = useRef<number | null>(null);

  const wsInitTokenRef = useRef<{ url: string; token: string } | null>(null);
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

    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    } catch {
      // ignore
    }
    streamRef.current = null;
    setStream(null);

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
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'violation',
          event_type: type,
          timestamp: new Date().toISOString(),
        }),
      );
    }
  }, []);

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
  }, []);

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
        startStreaming();
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
        // 1) Request fullscreen
        setStatus('fullscreen_pending');
        if (!document.fullscreenElement) {
          await document.documentElement.requestFullscreen();
        }

        // 2) Request webcam/mic permissions
        await requestMediaPermissions();

        // 3) Initialize session via API
        const sessionData = await withTimeout(
          proctoringService.initializeSession(assessmentAttemptId),
          15000,
          'Session initialization timed out',
        );

        if (!sessionData || !sessionData.session_id) {
          throw new Error('Failed to initialize proctoring session: Invalid response data');
        }

        sessionIdRef.current = sessionData.session_id;
        wsInitTokenRef.current = { url: sessionData.ws_url, token: sessionData.token };

        // 4) Connect WebSocket
        await connectWS(sessionData.ws_url, sessionData.token);
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
      return resp.data || resp;
    },
    enabled: !!sessionId,
  });
}

export function useProctoringEvidence(sessionId: string) {
  return useQuery({
    queryKey: ['proctoring-evidence', sessionId],
    queryFn: async () => {
      const resp = await proctoringService.getEvidence(sessionId);
      return resp.data || resp;
    },
    enabled: !!sessionId,
  });
}
