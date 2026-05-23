import { FileText, Search, Download, Loader2 } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, Button, Badge, LoadingState, ErrorState } from '../../components/ui';
import { useCandidates } from '../../hooks/useCandidates';
import { candidatesApi } from '../../api/candidates';
import { useState } from 'react';

export default function ResumeRepository() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [viewingId, setViewingId] = useState<string | null>(null);

  const { data: candidatesData, isLoading, error } = useCandidates({
    page,
    limit: 12,
    search: search || undefined,
    has_resume: true,
  });

  const candidates = candidatesData?.data || [];
  const totalItems = candidatesData?.pagination?.total ?? 0;

  const handleViewResume = async (id: string, name: string) => {
    try {
      setViewingId(id);
      console.log(`[ResumeRepository] Fetching resume for candidate: ${id}`);
      const blob = await candidatesApi.getResume(id);
      
      const url = URL.createObjectURL(blob);
      const isPdf = blob.type === 'application/pdf';
      
      if (isPdf) {
        window.open(url, '_blank');
      } else {
        // For DOCX/DOC, trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = `Resume_${name.replace(/\s+/g, '_')}${blob.type.includes('word') ? '.docx' : '.pdf'}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      
      // Clean up URL after a short delay
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
      console.error('[ResumeRepository] Failed to view resume:', err);
      alert('Failed to load resume. It might have been moved or deleted.');
    } finally {
      setViewingId(null);
    }
  };

  return (
    <AppShell title="Resume Repository">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div>
             <h1 className="text-2xl font-bold text-on-surface tracking-tight-display">Resume Repository</h1>
             <p className="text-sm text-tertiary">Access all uploaded candidate documents</p>
           </div>
        </div>

        <Card className="flex flex-col md:flex-row items-center gap-4">
           <div className="flex-1 relative w-full">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-tertiary" />
              <input 
                type="text"
                placeholder="Search by candidate name, skills, or email..."
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="w-full pl-10 pr-4 py-2 rounded-md bg-[var(--bg-layer1)] border border-[var(--border-ghost)] text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary/50"
              />
           </div>
           <div className="text-xs text-tertiary font-medium">
              Showing {candidates.length} of {totalItems} resumes
           </div>
        </Card>

        {isLoading ? (
          <LoadingState message="Loading documents..." />
        ) : error ? (
          <ErrorState message="Failed to load resume repository" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {candidates.map((c) => (
              <Card key={c.id} className="group hover:border-secondary/40 transition-colors flex flex-col h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-2.5 rounded-lg bg-secondary/10 text-secondary group-hover:bg-secondary group-hover:text-white transition-colors">
                    <FileText size={24} />
                  </div>
                  <Badge variant="info" className="text-[10px] uppercase">{c.branch}</Badge>
                </div>
                
                <h3 className="font-bold text-on-surface group-hover:text-secondary transition-colors truncate mb-1">
                  {c.name}
                </h3>
                <p className="text-xs text-tertiary truncate mb-4">{c.email}</p>
                
                <div className="mt-auto pt-4 border-t border-outline-variant flex items-center justify-end">
                   <Button 
                     variant="secondary" 
                     size="sm" 
                     onClick={() => handleViewResume(c.id, c.name)} 
                     isLoading={viewingId === c.id}
                     className="h-8 px-4 text-[10px] uppercase font-bold tracking-widest"
                   >
                      {viewingId === c.id ? <Loader2 size={12} className="animate-spin mr-1" /> : <Download size={12} className="mr-1" />}
                      View Resume
                   </Button>
                </div>
              </Card>
            ))}

            {candidates.length === 0 && (
               <div className="col-span-full py-20 text-center">
                  <FileText size={48} className="mx-auto text-tertiary opacity-20 mb-4" />
                  <p className="text-on-surface font-medium">No resumes uploaded yet</p>
                  <p className="text-sm text-tertiary mt-1">Uploaded candidate resumes will appear here.</p>
               </div>
            )}
          </div>
        )}

        {/* Simple Pagination */}
        {totalItems > 12 && (
           <div className="flex justify-center gap-2 pt-6">
              <Button 
                variant="secondary" 
                size="sm" 
                disabled={page === 1} 
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </Button>
              <div className="px-4 py-1.5 bg-secondary/10 rounded-md text-sm font-bold text-secondary">
                 Page {page}
              </div>
              <Button 
                variant="secondary" 
                size="sm" 
                disabled={candidates.length < 12} 
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </Button>
           </div>
        )}
      </div>
    </AppShell>
  );
}
