import { useState } from 'react';
import { useHiringCycles } from '../../hooks/useHiringCycles';
import { hiringCyclesApi } from '../../api/hiring-cycles';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Button } from '../../components/ui';

export default function CycleConfig() {
  const { data: cycles, isLoading: _isLoading } = useHiringCycles();
  const [selected, setSelected] = useState<string | null>(null);
  const [jsonText, setJsonText] = useState('');
  const [saving, setSaving] = useState(false);
  const cycleList = Array.isArray(cycles) ? cycles : [];

  const onSelect = (id: string) => {
    setSelected(id);
    const c = cycleList.find((x: any) => x.id === id);
    setJsonText(JSON.stringify(c?.proctoring_config || {}, null, 2));
  };

  const onSave = async () => {
    if (!selected) return;
    let parsed = {};
    try {
      parsed = JSON.parse(jsonText || '{}');
    } catch (e) {
      alert('Invalid JSON');
      return;
    }
    setSaving(true);
    try {
      await hiringCyclesApi.update(selected, { proctoring_config: parsed });
      alert('Saved');
    } catch (err: any) {
      alert('Save failed: ' + (err.message || String(err)));
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell title="Cycle Config">
      <div className="max-w-4xl">
        <Card>
          <h2 className="text-lg font-bold">Proctoring Configuration</h2>
          <p className="text-sm text-tertiary">Select a hiring cycle and edit its proctoring configuration (JSON).</p>

          <div className="mt-4 flex gap-3">
            <select className="p-2 border rounded" onChange={(e) => onSelect(e.target.value)} value={selected || ''}>
              <option value="">-- Select Cycle --</option>
              {cycleList.map((c: any) => (
                <option key={c.id} value={c.id}>{c.name} ({c.status})</option>
              ))}
            </select>
            <Button onClick={() => {
              if (cycleList.length) onSelect(cycleList[0].id);
            }}>Load first</Button>
          </div>

          <div className="mt-4">
            <textarea className="w-full h-64 p-2 border rounded" value={jsonText} onChange={(e) => setJsonText(e.target.value)} />
          </div>

          <div className="mt-3 flex justify-end">
            <Button onClick={onSave} isLoading={saving}>Save</Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
