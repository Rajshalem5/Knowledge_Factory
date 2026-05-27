import { useState } from 'react';
import { Upload, History, AlertCircle, ArrowRight, Database } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardTitle, Button, LoadingState, ErrorState, EmptyState } from '../../components/ui';
import { BulkUploadModal } from '../../components/admin/BulkUploadModal';
import { usePipelineStats } from '../../hooks/useScreening';

export default function UploadCenter() {
  const [isBulkUploadModalOpen, setIsBulkUploadModalOpen] = useState(false);
  
  const { data: statsData, isLoading: statsLoading, error: statsError } = usePipelineStats();

  // Real data from pipeline stats if available
  const totalCandidates = statsData?.aggregates?.total_filtered ?? 0;
  const successRate = statsData?.aggregates?.assessment_completion_rate ?? 0;

  return (
    <AppShell title="Upload Center">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div>
             <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Candidate Ingestion</h1>
             <p className="text-sm text-tertiary">Process bulk candidate records and resumes</p>
           </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Upload Area */}
          <Card className="lg:col-span-2 flex flex-col items-center justify-center p-12 border-2 border-dashed border-secondary/20 bg-secondary/5 hover:bg-secondary/10 transition-colors cursor-pointer group" onClick={() => setIsBulkUploadModalOpen(true)}>
             <div className="p-4 rounded-full bg-secondary/20 text-secondary mb-6 group-hover:scale-110 transition-transform">
                <Upload size={40} />
             </div>
             <h2 className="text-xl font-bold text-on-surface mb-2">Bulk Upload Candidates</h2>
             <p className="text-sm text-tertiary text-center max-w-sm mb-8">
                Upload your candidate sheets (CSV, XLSX) or a collection of resumes (PDF, DOCX). 
                The system will automatically validate and create profiles.
             </p>
             <Button size="lg">
                Start New Ingestion
                <ArrowRight size={18} />
             </Button>
          </Card>

          {/* Stats / Info */}
          <div className="space-y-6">
             <Card>
                <CardTitle className="text-sm mb-4 flex items-center gap-2">
                   <Database size={16} className="text-secondary" />
                   Ingestion Overview
                </CardTitle>
                {statsLoading ? (
                   <div className="py-4"><LoadingState /></div>
                ) : statsError ? (
                   <ErrorState message="Failed to load stats" />
                ) : (
                   <div className="space-y-4">
                      <div className="flex justify-between items-center pb-3 border-b border-outline-variant">
                         <span className="text-xs text-tertiary">Total Ingested</span>
                         <span className="font-bold text-on-surface">{totalCandidates.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between items-center pb-3 border-b border-outline-variant">
                         <span className="text-xs text-tertiary">Active Pipeline</span>
                         <span className="font-bold text-secondary">{totalCandidates}</span>
                      </div>
                      <div className="flex justify-between items-center">
                         <span className="text-xs text-tertiary">Success Rate</span>
                         <span className="font-bold text-success">{successRate > 0 ? `${successRate}%` : '100%'}</span>
                      </div>
                   </div>
                )}
             </Card>

             <Card className="bg-info-container/10 border-info/20">
                <div className="flex gap-3">
                   <AlertCircle size={20} className="text-info shrink-0" />
                   <div>
                      <p className="text-xs font-bold text-info-on-container uppercase tracking-architectural">Duplicate Detection</p>
                      <p className="text-[11px] text-info-on-container/80 mt-1">
                         The system automatically identifies duplicates based on email and phone numbers.
                         Existing records will be updated with new data.
                      </p>
                   </div>
                </div>
             </Card>
          </div>
        </div>

        {/* Upload History */}
        <Card padding="none">
           <div className="p-4 border-b border-outline-variant bg-[var(--bg-layer1)]">
              <CardTitle className="text-base flex items-center gap-2">
                 <History size={18} className="text-secondary" />
                 Recent Ingestions
              </CardTitle>
           </div>
           <div className="overflow-hidden">
              <EmptyState 
                icon={History}
                title="No uploads yet"
                description="Upload candidate resumes or spreadsheets to begin."
              />
              <div className="pb-12 text-center">
                 <Button variant="secondary" size="sm" onClick={() => setIsBulkUploadModalOpen(true)}>
                    <Upload size={14} />
                    Upload Files
                 </Button>
              </div>
           </div>
        </Card>
      </div>

      <BulkUploadModal 
        open={isBulkUploadModalOpen} 
        onClose={() => setIsBulkUploadModalOpen(false)} 
      />
    </AppShell>
  );
}
