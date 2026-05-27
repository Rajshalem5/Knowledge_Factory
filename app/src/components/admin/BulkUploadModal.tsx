import { useState, useRef, useEffect } from 'react';
import { Upload, X, AlertCircle, CheckCircle, FileText, Zap, Info } from 'lucide-react';
import { Modal, Button, Input, Badge } from '../ui';
import { useBulkUpload, usePreviewBulkUpload } from '../../hooks/useCandidates';
import type { BulkUploadPreview, BulkUploadResponse } from '../../types';

interface BulkUploadModalProps {
  open: boolean;
  onClose: () => void;
}

export function BulkUploadModal({ open, onClose }: BulkUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BulkUploadPreview | null>(null);
  const [result, setResult] = useState<BulkUploadResponse | null>(null);
  const [editableData, setEditableData] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const previewMutation = usePreviewBulkUpload();
  const uploadMutation = useBulkUpload();

  useEffect(() => {
    if (preview && preview.total_records === 1 && preview.preview[0]?.data?.is_ai_parsed) {
      setEditableData(preview.preview[0].data);
    } else {
      setEditableData(null);
    }
  }, [preview]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      try {
        const res = await previewMutation.mutateAsync(selectedFile);
        setPreview(res);
      } catch (err) {
        console.error('[BulkUploadModal] Preview failed:', err);
      }
    }
  };

  const handleUpload = async () => {
    if (file) {
      try {
        // If we have editableData (AI parsed), we send it to bypass re-parsing on server
        const res = await uploadMutation.mutateAsync({ file, data: editableData });
        setResult(res as unknown as BulkUploadResponse);
      } catch (err) {
        console.error('[BulkUploadModal] Upload failed:', err);
      }
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setEditableData(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const isAiParsed = preview?.preview[0]?.data?.is_ai_parsed;

  return (
    <Modal open={open} onClose={onClose} title={isAiParsed ? "AI Resume Extraction" : "Candidate Ingestion"}>
      <div className="space-y-4">
        {!file ? (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-[var(--border-ghost)] rounded-lg p-10 flex flex-col items-center justify-center cursor-pointer hover:border-secondary/50 hover:bg-secondary/5 transition-all"
          >
            <Upload size={32} className="text-tertiary mb-3" />
            <p className="text-sm font-medium text-on-surface">Click to upload file</p>
            <p className="text-xs text-tertiary mt-1 text-center">
              Supports CSV, XLSX, PDF, and DOCX<br/>
              (Structured sheets or individual resumes)
            </p>
            <input 
              ref={fileInputRef}
              type="file" 
              accept=".csv,.xlsx,.xls,.pdf,.doc,.docx" 
              className="hidden" 
              onChange={handleFileChange} 
            />
          </div>
        ) : (
          <div className="space-y-4">
            {/* File Info Header */}
            <div className="flex items-center justify-between p-3 bg-[var(--bg-layer1)] rounded-md border border-[var(--border-ghost)]">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-secondary/10 rounded">
                  <FileText size={18} className="text-secondary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-on-surface truncate max-w-[200px]">{file.name}</p>
                  <p className="text-xs text-tertiary">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              {!result && (
                <button onClick={reset} className="p-1 hover:text-danger transition-colors">
                  <X size={16} />
                </button>
              )}
            </div>

            {previewMutation.isPending && (
              <div className="py-8 text-center space-y-3">
                <div className="flex justify-center">
                   <Zap size={32} className="text-secondary animate-pulse" />
                </div>
                <p className="text-sm text-on-surface font-medium animate-pulse">Running AI Extraction...</p>
                <p className="text-[10px] text-tertiary uppercase tracking-architectural">This takes ~10 seconds</p>
              </div>
            )}

            {preview && !previewMutation.isPending && !result && (
              <div className="space-y-4">
                {isAiParsed && editableData ? (
                  /* AI Extraction View */
                  <div className="space-y-4 max-h-[400px] overflow-y-auto px-1">
                     <div className="flex items-center gap-2 text-secondary">
                        <Zap size={14} />
                        <span className="text-[10px] font-bold uppercase tracking-widest">Extracted Candidate Details</span>
                     </div>
                     
                     <div className="grid grid-cols-2 gap-4">
                        <Input 
                          label="Full Name" 
                          value={editableData.name} 
                          onChange={e => setEditableData({...editableData, name: e.target.value})}
                        />
                        <Input 
                          label="Email Address" 
                          value={editableData.email} 
                          onChange={e => setEditableData({...editableData, email: e.target.value})}
                        />
                        <Input 
                          label="Degree" 
                          value={editableData.degree} 
                          onChange={e => setEditableData({...editableData, degree: e.target.value})}
                          placeholder="e.g. B.Tech, MCA"
                        />
                        <Input 
                          label="Branch / Specialization" 
                          value={editableData.branch} 
                          onChange={e => setEditableData({...editableData, branch: e.target.value})}
                        />
                        <Input 
                          label="College / Institute" 
                          value={editableData.college} 
                          onChange={e => setEditableData({...editableData, college: e.target.value})}
                        />
                        <div className="grid grid-cols-2 gap-2">
                           <Input 
                             label="CGPA" 
                             type="number"
                             step="0.01"
                             value={editableData.cgpa} 
                             onChange={e => setEditableData({...editableData, cgpa: e.target.value})}
                           />
                           <Input 
                             label="Batch" 
                             type="number"
                             value={editableData.passed_out_year} 
                             onChange={e => setEditableData({...editableData, passed_out_year: e.target.value})}
                           />
                        </div>
                     </div>

                     <div>
                        <label className="block text-[10px] font-bold uppercase tracking-widest text-tertiary mb-1.5 ml-1">Extracted Skills</label>
                        <div className="flex flex-wrap gap-1.5 p-3 rounded-md bg-[var(--bg-layer1)] border border-[var(--border-ghost)]">
                           {editableData.skills?.split(',').map((s: string, i: number) => (
                             <Badge key={i} variant="info" className="text-[10px]">{s.trim()}</Badge>
                           ))}
                           {(!editableData.skills || editableData.skills.length < 2) && <span className="text-xs text-tertiary italic">No skills detected</span>}
                        </div>
                     </div>

                     <div className="p-3 bg-info/5 border border-info/10 rounded-md">
                        <p className="text-[10px] text-info-on-container leading-relaxed">
                           <AlertCircle size={10} className="inline mr-1" />
                           Please verify the extracted information. AI extraction may occasionally misidentify fields depending on resume layout.
                        </p>
                     </div>
                  </div>
                ) : (
                  /* Standard CSV/XLSX Stats View */
                  <div className="space-y-3">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 bg-secondary/5 rounded-md border border-secondary/10">
                        <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Total</p>
                        <p className="text-lg font-bold text-on-surface">{preview.total_records}</p>
                      </div>
                      <div className="p-3 bg-success/5 rounded-md border border-success/10">
                        <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Valid</p>
                        <p className="text-lg font-bold text-success">{preview.valid_records}</p>
                      </div>
                      <div className="p-3 bg-danger/5 rounded-md border border-danger/10">
                        <p className="text-xs text-tertiary uppercase tracking-architectural mb-1">Errors</p>
                        <p className="text-lg font-bold text-danger">{preview.invalid_records}</p>
                      </div>
                    </div>

                    {preview.errors.length > 0 && (
                      <div className="p-3 bg-danger/5 rounded-md border border-danger/10 max-h-32 overflow-y-auto">
                        <div className="flex items-center gap-2 text-danger mb-2">
                          <AlertCircle size={14} />
                          <span className="text-xs font-bold uppercase tracking-architectural">Validation Errors</span>
                        </div>
                        <ul className="space-y-1">
                          {preview.errors.slice(0, 5).map((err, i) => (
                            <li key={i} className="text-xs text-danger/80">
                              Row {err.row}: {err.error}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {result && (
              <div className="space-y-4">
                 <div className="p-4 bg-secondary/5 border border-secondary/20 rounded-md flex flex-col items-center gap-2 text-center">
                    <CheckCircle size={32} className="text-success" />
                    <div>
                       <p className="text-sm font-bold text-on-surface">Ingestion Processed</p>
                       <p className="text-xs text-tertiary mt-1">Batch ID: {result.batch_id}</p>
                    </div>
                 </div>

                 <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 bg-success/10 border border-success/20 rounded-md text-center">
                       <p className="text-[10px] text-success-on-container uppercase font-bold tracking-widest mb-1">Created</p>
                       <p className="text-xl font-black text-success">{result.created}</p>
                    </div>
                    <div className="p-3 bg-warning/10 border border-warning/20 rounded-md text-center">
                       <p className="text-[10px] text-warning-on-container uppercase font-bold tracking-widest mb-1">Skipped</p>
                       <p className="text-xl font-black text-warning">{result.skipped}</p>
                    </div>
                    <div className="p-3 bg-danger/10 border border-danger/20 rounded-md text-center">
                       <p className="text-[10px] text-danger-on-container uppercase font-bold tracking-widest mb-1">Failed</p>
                       <p className="text-xl font-black text-danger">{result.errors.length}</p>
                    </div>
                 </div>

                 {(result.duplicates.length > 0 || result.errors.length > 0) && (
                    <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                       {result.duplicates.map((dup, i) => (
                          <div key={`dup-${i}`} className="flex items-center gap-2 p-2 rounded bg-warning/5 border border-warning/10 text-[10px]">
                             <Info size={12} className="text-warning" />
                             <span className="font-bold text-warning-on-container">{dup.email}</span>
                             <span className="text-tertiary ml-auto">{dup.reason}</span>
                          </div>
                       ))}
                       {result.errors.map((err, i) => (
                          <div key={`err-${i}`} className="flex items-center gap-2 p-2 rounded bg-danger/5 border border-danger/10 text-[10px]">
                             <AlertCircle size={12} className="text-danger" />
                             <span className="font-bold text-danger-on-container">Row {err.row}</span>
                             <span className="text-tertiary ml-auto truncate">{err.error}</span>
                          </div>
                       ))}
                    </div>
                 )}

                 <Button className="w-full" onClick={() => { onClose(); reset(); }}>
                    Finish & Close
                 </Button>
              </div>
            )}

            {!result && (
              <div className="flex justify-end gap-3 pt-2 border-t border-[var(--border-ghost)]">
                <Button variant="secondary" onClick={onClose}>Cancel</Button>
                <Button 
                  onClick={handleUpload} 
                  disabled={!preview || (preview.valid_records === 0 && !isAiParsed) || uploadMutation.isPending || previewMutation.isPending}
                  isLoading={uploadMutation.isPending}
                >
                  {isAiParsed ? 'Confirm & Create Profile' : 'Confirm & Upload'}
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}

