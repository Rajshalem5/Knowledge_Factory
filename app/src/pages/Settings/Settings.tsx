import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export default function Settings() {
  const { user, logout } = useAuth();
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showDelete, setShowDelete] = useState(false);
  const [status, setStatus] = useState<{type: 'success' | 'error', msg: string} | null>(null);

  const handleDeleteAccount = async () => {
    if (!confirmPassword) {
      setStatus({ type: 'error', msg: 'Please enter your password to confirm.' });
      return;
    }
    try {
      // Step 1: confirm-password → returns { verified, user_id }
      const verifyRes = await fetch('/api/auth/confirm-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('kf_token') || ''}`,
        },
        body: JSON.stringify({ password: confirmPassword }),
        credentials: 'include',
      });
      if (!verifyRes.ok) throw new Error('Password verification failed');
      const verifyData = await verifyRes.json() as { verified: boolean; user_id: string };
      // Step 2: delete-account using the verified user_id as the reauth token
      const delRes = await fetch('/api/auth/delete-account', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('kf_token') || ''}`,
        },
        body: JSON.stringify({ reauth_token: verifyData.user_id }),
        credentials: 'include',
      });
      if (!delRes.ok) throw new Error('Account deletion failed');
      logout();
    } catch (e: unknown) {
      setStatus({ type: 'error', msg: e instanceof Error ? e.message : 'Failed to delete account' });
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '40px 20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '24px', color: '#e0e0f0' }}>Settings</h1>

      <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: '#a0a0c0' }}>Account</h2>
        <div style={{ display: 'grid', gap: '12px' }}>
          <div>
            <span style={{ color: '#606080', fontSize: '13px' }}>Name</span>
            <p style={{ margin: '4px 0 0', color: '#e0e0f0' }}>{user?.name || 'N/A'}</p>
          </div>
          <div>
            <span style={{ color: '#606080', fontSize: '13px' }}>Email</span>
            <p style={{ margin: '4px 0 0', color: '#e0e0f0' }}>{user?.email || 'N/A'}</p>
          </div>
          <div>
            <span style={{ color: '#606080', fontSize: '13px' }}>Role</span>
            <p style={{ margin: '4px 0 0', color: '#8b5cf6', textTransform: 'capitalize' }}>{user?.role || 'N/A'}</p>
          </div>
        </div>
      </div>

      <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px', border: '1px solid #ff4d4d33' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px', color: '#ff6b6b' }}>Danger Zone</h2>
        <p style={{ color: '#8080a0', fontSize: '14px', marginBottom: '16px' }}>
          Permanently delete your account and all associated candidate data. This action cannot be undone.
        </p>
        {!showDelete ? (
          <button
            onClick={() => setShowDelete(true)}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              border: '1px solid #ff4d4d',
              background: 'transparent',
              color: '#ff6b6b',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Delete Account
          </button>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              type="password"
              placeholder="Enter your password to confirm"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                border: '1px solid #3d3d5c',
                background: '#12121e',
                color: '#e0e0f0',
                fontSize: '14px',
              }}
            />
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleDeleteAccount}
                style={{
                  padding: '10px 20px',
                  borderRadius: '8px',
                  border: 'none',
                  background: '#ff4d4d',
                  color: '#fff',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Confirm Delete
              </button>
              <button
                onClick={() => { setShowDelete(false); setConfirmPassword(''); }}
                style={{
                  padding: '10px 20px',
                  borderRadius: '8px',
                  border: '1px solid #3d3d5c',
                  background: 'transparent',
                  color: '#a0a0c0',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        {status && (
          <p style={{ marginTop: '12px', color: status.type === 'error' ? '#ff6b6b' : '#4ade80', fontSize: '14px' }}>
            {status.msg}
          </p>
        )}
      </div>
    </div>
  );
}