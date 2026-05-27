import React, { useRef, useEffect } from 'react';
import { Badge, Button } from '../ui';
import { Camera, Mic, Wifi, ShieldAlert, Loader2 } from 'lucide-react';

interface ProctoringOverlayProps {
  status: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  riskScore: number;
  isWebcamActive: boolean;
  isMicActive: boolean;
  connectionStatus: string;
  stream: MediaStream | null;
  onRetry?: () => void;
}

const STATUS_MESSAGES: Record<string, { label: string; icon: React.ReactNode }> = {
  idle: { label: 'Proctoring ready to start', icon: <Camera size={14} /> },
  waiting_permissions: { label: 'Requesting camera & microphone access...', icon: <Loader2 size={14} className="animate-spin" /> },
  fullscreen_pending: { label: 'Switching to fullscreen...', icon: <Loader2 size={14} className="animate-spin" /> },
  connecting_websocket: { label: 'Connecting to proctoring server...', icon: <Loader2 size={14} className="animate-spin" /> },
  ready: { label: 'Proctoring active', icon: <Camera size={14} /> },
  failed: { label: 'Proctoring failed', icon: <ShieldAlert size={14} /> },
  terminated: { label: 'Assessment terminated', icon: <ShieldAlert size={14} /> },
};

export const ProctoringOverlay: React.FC<ProctoringOverlayProps> = ({
  status,
  riskLevel,
  riskScore,
  isWebcamActive,
  isMicActive,
  connectionStatus,
  stream,
  onRetry,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && stream && status === 'ready') {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch(err => {
        console.warn('[ProctoringOverlay] Video play failed:', err);
      });
    }
  }, [stream, status]);

  // Don't render anything when idle (before start)
  if (status === 'idle') {
    return null;
  }

  // Pre-ready states: show minimal status indicator
  if (status === 'waiting_permissions' || status === 'fullscreen_pending' || status === 'connecting_websocket') {
    const msg = STATUS_MESSAGES[status];
    return (
      <div className="fixed bottom-4 right-4 bg-[var(--bg-layer2)] p-3 rounded-lg shadow-xl border border-outline-variant z-50">
        <div className="flex items-center gap-3">
          <div className="text-secondary">{msg.icon}</div>
          <span className="text-xs font-medium text-on-surface">{msg.label}</span>
        </div>
      </div>
    );
  }

  // Failed state: show error with optional retry
  if (status === 'failed') {
    return (
      <div className="fixed bottom-4 right-4 bg-[var(--bg-layer2)] p-4 rounded-lg shadow-xl border border-danger/50 z-50 min-w-[220px]">
        <div className="flex items-center gap-2 mb-3">
          <ShieldAlert size={16} className="text-danger" />
          <span className="text-xs font-bold text-danger uppercase tracking-widest">Proctoring failed</span>
        </div>
        <p className="text-[11px] text-on-surface-variant mb-3">
          Camera, microphone, or connection error. You can retry or continue without proctoring.
        </p>
        {onRetry && (
          <Button size="sm" variant="secondary" onClick={onRetry} className="w-full">
            <Camera size={12} />
            Retry Proctoring
          </Button>
        )}
      </div>
    );
  }

  // Terminated state
  if (status === 'terminated') {
    return (
      <div className="fixed bottom-4 right-4 bg-[var(--bg-layer2)] p-3 rounded-lg shadow-xl border border-danger/50 z-50">
        <div className="flex items-center gap-2">
          <ShieldAlert size={14} className="text-danger" />
          <span className="text-xs font-medium text-danger">Assessment terminated</span>
        </div>
      </div>
    );
  }

  // Ready state: show the full proctoring UI
  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-3 z-50 pointer-events-none">
      
      {/* 1. Webcam Mini Preview */}
      <div className="w-48 h-36 bg-black rounded-lg overflow-hidden border-2 border-outline-variant shadow-2xl relative">
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="w-full h-full object-cover mirror"
        />
        {!isWebcamActive && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80">
            <ShieldAlert className="text-danger" size={32} />
          </div>
        )}
        
        {/* Indicators Overlay */}
        <div className="absolute top-2 right-2 flex flex-col gap-1.5">
          <div className={`p-1 rounded-full ${isMicActive ? 'bg-secondary/20 text-secondary' : 'bg-danger/20 text-danger'}`}>
            <Mic size={12} />
          </div>
          <div className={`p-1 rounded-full ${connectionStatus === 'connected' ? 'bg-secondary/20 text-secondary' : 'bg-warning/20 text-warning'}`}>
            <Wifi size={12} />
          </div>
        </div>

        {/* Risk Badge */}
        <div className="absolute bottom-2 left-2">
          <Badge variant={riskLevel === 'LOW' ? 'success' : riskLevel === 'MEDIUM' ? 'warning' : 'danger'}>
            {riskLevel} RISK
          </Badge>
        </div>
      </div>

      {/* 2. Status Card */}
      <div className="bg-[var(--bg-layer2)]/90 backdrop-blur-md p-3 rounded-lg shadow-lg border border-outline-variant pointer-events-auto">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-tertiary">Live Proctoring</span>
          <span className="text-xs font-mono text-on-surface">{Math.round(riskScore)}%</span>
        </div>
        
        <div className="w-full h-1 bg-outline-variant rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${
              riskLevel === 'LOW' ? 'bg-secondary' : riskLevel === 'MEDIUM' ? 'bg-warning' : 'bg-danger'
            }`}
            style={{ width: `${riskScore}%` }}
          />
        </div>

        {riskLevel === 'HIGH' && (
          <div className="mt-2 flex items-center gap-2 text-danger animate-bounce">
            <ShieldAlert size={14} />
            <span className="text-[10px] font-bold uppercase">Severe Violation Warning</span>
          </div>
        )}
      </div>
    </div>
  );
};
