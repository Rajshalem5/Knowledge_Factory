import { useState, useEffect } from 'react';

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    setVisible(false);
  };

  const decline = () => {
    localStorage.setItem('cookie_consent', 'declined');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      background: '#1a1a2e',
      borderTop: '1px solid #2d2d4a',
      padding: '16px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
      zIndex: 9999,
      flexWrap: 'wrap',
    }}>
      <p style={{ margin: 0, color: '#a0a0c0', fontSize: '14px', flex: 1, minWidth: '200px' }}>
        We use cookies to improve your experience and analyze site usage.{' '}
        <a href="/privacy" style={{ color: '#8b5cf6' }}>Privacy Policy</a>
      </p>
      <div style={{ display: 'flex', gap: '12px', flexShrink: 0 }}>
        <button
          onClick={decline}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: '1px solid #3d3d5c',
            background: 'transparent',
            color: '#a0a0c0',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Decline
        </button>
        <button
          onClick={accept}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: 'none',
            background: '#8b5cf6',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          Accept
        </button>
      </div>
    </div>
  );
}