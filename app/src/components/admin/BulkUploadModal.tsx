
import { useState, useRef } from 'react';
import { Upload, X, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import { Modal, Button } from '../ui';
import { useBulkUpload, usePreviewBulkUpload } from '../../hooks/useCandidates';
import type { BulkUploadPreview } from '../../types';

interface BulkUploadModalProps {
  open: boolean;
  onClose: () => void;
}

export function BulkUploadModal({ open, onClose }: BulkUploadModalProps) {
  console.log('[BulkUploadModal] Rendering, open:', open);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BulkUploadPreview | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const previewMutation = usePreviewBulkUpload();
  const uploadMutation = useBulkUpload();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    console.log('[BulkUploadModal] File selected:', selectedFile?.name);
    if (selectedFile) {
      setFile(selectedFile);
      try {
        console.log('[BulkUploadModal] Requesting preview...');
        const res = await previewMutation.mutateAsync(selectedFile);
        console.log('[BulkUploadModal] Preview received:', res);
        setPreview(res);
      } catch (err) {
        console.error('[BulkUploadModal] Preview failed:', err);
      }
    }
  };

  const handleUpload = async () => {
    console.log('[BulkUploadModal] Upload button clicked');
    if (file) {
      try {
        console.log('[BulkUploadModal] Starting upload...');
        await uploadMutation.mutateAsync(file);
        console.log('[BulkUploadModal] Upload success');
        setIsSuccess(true);
        setTimeout(() => {
          onClose();
          reset();
        }, 2000);
      } catch (err) {
        console.error('[BulkUploadModal] Upload failed:', err);
      }
    }
  };

  const reset = () => {
    console.log('[BulkUploadModal] Resetting state');
    setFile(null);
    setPreview(null);
    setIsSuccess(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Modal open={open} onClose={onClose} title="Candidate Ingestion">
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
            <div className="flex items-center justify-between p-3 bg-[var(--bg-layer1)] rounded-md border border-[var(--border-ghost)]">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-secondary/10 rounded">
                  <FileText size={18} className="text-secondary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-on-surface">{file.name}</p>
                  <p className="text-xs text-tertiary">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <button onClick={reset} className="p-1 hover:text-danger transition-colors">
                <X size={16} />
              </button>
            </div>

            {previewMutation.isPending && (
              <div className="py-4 text-center">
                <p className="text-sm text-tertiary animate-pulse">Validating records...</p>
              </div>
            )}

            {preview && (
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
                      {preview.errors.length > 5 && (
                        <li className="text-[10px] text-tertiary italic">
                          ...and {preview.errors.length - 5} more errors
                        </li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {isSuccess ? (
              <div className="p-4 bg-success/10 border border-success/20 rounded-md flex items-center gap-3 text-success">
                <CheckCircle size={20} />
                <div>
                  <p className="text-sm font-bold">Upload Successful!</p>
                  <p className="text-xs opacity-80">Candidates have been added to the pipeline.</p>
                </div>
              </div>
            ) : (
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={onClose}>Cancel</Button>
                <Button 
                  onClick={handleUpload} 
                  disabled={!preview || preview.valid_records === 0 || uploadMutation.isPending}
                  isLoading={uploadMutation.isPending}
                >
                  Confirm & Upload
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
