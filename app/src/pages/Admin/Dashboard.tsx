import { useState } from 'react';
import { adminApi } from '../../api/admin';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'logs' | 'export'>('logs');
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [exportStatus, setExportStatus] = useState<string>('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getAuditLogs(1, 100);
      setLogs(data.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleExport = async () => {
    setExportStatus('Exporting...');
    try {
      const data = await adminApi.exportDatabase();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kf_export_${new Date().toISOString().slice(0,10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportStatus('Export downloaded.');
    } catch (e) {
      setExportStatus('Export failed: ' + (e as Error).message);
    }
  };

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '24px', color: '#e0e0f0' }}>Admin Dashboard</h1>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        <button
          onClick={() => { setActiveTab('logs'); fetchLogs(); }}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: activeTab === 'logs' ? '1px solid #8b5cf6' : '1px solid #3d3d5c',
            background: activeTab === 'logs' ? '#8b5cf620' : 'transparent',
            color: activeTab === 'logs' ? '#a78bfa' : '#8080a0',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Audit Logs
        </button>
        <button
          onClick={() => { setActiveTab('export'); }}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: activeTab === 'export' ? '1px solid #8b5cf6' : '1px solid #3d3d5c',
            background: activeTab === 'export' ? '#8b5cf620' : 'transparent',
            color: activeTab === 'export' ? '#a78bfa' : '#8080a0',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          Export DB
        </button>
      </div>

      {activeTab === 'logs' && (
        <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '20px' }}>
          {loading ? (
            <p style={{ color: '#8080a0' }}>Loading...</p>
          ) : logs.length === 0 ? (
            <p style={{ color: '#8080a0' }}>No audit logs yet.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2d2d4a', textAlign: 'left' }}>
                    <th style={{ padding: '8px 12px', color: '#606080' }}>Action</th>
                    <th style={{ padding: '8px 12px', color: '#606080' }}>Entity</th>
                    <th style={{ padding: '8px 12px', color: '#606080' }}>User</th>
                    <th style={{ padding: '8px 12px', color: '#606080' }}>IP</th>
                    <th style={{ padding: '8px 12px', color: '#606080' }}>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id} style={{ borderBottom: '1px solid #22223a' }}>
                      <td style={{ padding: '8px 12px', color: '#8b5cf6' }}>{log.action}</td>
                      <td style={{ padding: '8px 12px', color: '#e0e0f0' }}>{log.entity_type}:{log.entity_id}</td>
                      <td style={{ padding: '8px 12px', color: '#a0a0c0' }}>{log.user_id}</td>
                      <td style={{ padding: '8px 12px', color: '#606080' }}>{log.ip_address}</td>
                      <td style={{ padding: '8px 12px', color: '#606080' }}>{log.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'export' && (
        <div style={{ background: '#1a1a2e', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#e0e0f0' }}>Database Export</h2>
          <p style={{ color: '#8080a0', marginBottom: '20px', fontSize: '14px' }}>
            Download a JSON snapshot of all users, candidates, assessments, scores, and hiring cycles. Admin access required.
          </p>
          <button
            onClick={handleExport}
            style={{
              padding: '10px 24px',
              borderRadius: '8px',
              border: 'none',
              background: '#8b5cf6',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 600,
            }}
          >
            Download DB Export
          </button>
          {exportStatus && (
            <p style={{ marginTop: '12px', color: '#4ade80', fontSize: '14px' }}>{exportStatus}</p>
          )}
        </div>
      )}
    </div>
  );
}