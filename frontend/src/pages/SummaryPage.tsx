import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ClipboardCheck, 
  Check, 
  X, 
  Edit3, 
  ShieldAlert, 
  RefreshCw, 
  Sparkles, 
  UserCheck, 
  AlertCircle,
  FileCheck,
  CheckCircle2,
  Info
} from 'lucide-react';
import { 
  getSummary, 
  generateSummary, 
  editSummary, 
  acceptSummary, 
  rejectSummary, 
  SummaryData 
} from '../api/client';

export const SummaryPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const paramSessionId = searchParams.get('session_id');
  const [sessionId, setSessionId] = useState<string>(
    paramSessionId || localStorage.getItem('active_session_id') || ''
  );
  const [editing, setEditing] = useState<boolean>(false);
  const [editedText, setEditedText] = useState<string>('');
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [notesModalOpen, setNotesModalOpen] = useState<boolean>(false);
  const [physicianNotes, setPhysicianNotes] = useState<string>('');

  const queryClient = useQueryClient();

  React.useEffect(() => {
    if (paramSessionId && paramSessionId !== sessionId) {
      setSessionId(paramSessionId);
    } else if (!paramSessionId) {
      const stored = localStorage.getItem('active_session_id');
      if (stored && stored !== sessionId) setSessionId(stored);
    }
  }, [paramSessionId]);

  // Query summary — only when we have a real session ID
  const { data: summary, isLoading, isError, refetch } = useQuery<SummaryData>({
    queryKey: ['clinicalSummary', sessionId],
    queryFn: () => getSummary(sessionId),
    retry: false,
    enabled: !!sessionId,
  });

  // Mutations
  const generateMutation = useMutation({
    mutationFn: () => generateSummary(sessionId),
    onSuccess: (data) => {
      queryClient.setQueryData(['clinicalSummary', sessionId], data);
    },
  });

  const editMutation = useMutation({
    mutationFn: (newText: string) => {
      const active = summary?.active_summary || {};
      const updated = { session_id: sessionId, ...active, generated_summary_text: newText };
      return editSummary(sessionId, updated);
    },
    onSuccess: (data) => {
      setEditing(false);
      queryClient.setQueryData(['clinicalSummary', sessionId], data);
    },
  });

  const acceptMutation = useMutation({
    mutationFn: () => acceptSummary(sessionId, physicianNotes),
    onSuccess: (data) => {
      setNotesModalOpen(false);
      queryClient.setQueryData(['clinicalSummary', sessionId], data);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectSummary(sessionId, rejectReason),
    onSuccess: (data) => {
      setRejectModalOpen(false);
      queryClient.setQueryData(['clinicalSummary', sessionId], data);
    },
  });

  const activeSummary = summary?.active_summary || {};
  const isPhysicianEdited = !!summary?.physician_edited_summary;
  const isAccepted = summary?.workflow_status === 'ACCEPTED';
  const isRejected = summary?.workflow_status === 'REJECTED';

  // Guard: no active session
  if (!sessionId) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto">
        <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">No Active Session</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
              Please start a pre-consultation session first before generating a clinical summary.
            </p>
          </div>
          <button
            onClick={() => navigate('/identify')}
            className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-500/20 transition-all"
          >
            Start a New Session
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <ClipboardCheck className="w-7 h-7 text-brand-400" /> Structured Clinical Summary & Review
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Synthesized clinical history review powered by Module C LLM interpretation & Pydantic validation.
          </p>
        </div>

        {/* Workflow Status Badge */}
        <div className="flex items-center gap-3">
          {summary ? (
            <span className={`px-3.5 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 border ${
              isAccepted
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : isRejected
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}>
              {isAccepted ? <CheckCircle2 className="w-3.5 h-3.5" /> : isRejected ? <AlertCircle className="w-3.5 h-3.5" /> : <Sparkles className="w-3.5 h-3.5" />}
              {summary.workflow_status}
            </span>
          ) : (
            <span className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
              NOT GENERATED
            </span>
          )}

          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-medium transition-all shadow-md"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generateMutation.isPending ? 'animate-spin' : ''}`} />
            <span>{summary ? 'Regenerate Summary' : 'Generate Summary'}</span>
          </button>
        </div>
      </div>

      {/* Session ID Selector / Demo Helper Bar */}
      <div className="glass-card p-3 rounded-xl flex items-center justify-between text-xs border border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">Target Session ID:</span>
          <input
            type="text"
            value={sessionId}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSessionId(e.target.value)}
            className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 font-mono focus:outline-none focus:border-brand-500"
          />

        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <span>AI Model: <strong className="text-brand-300 font-mono">{summary?.llm_model || 'mock-llm'}</strong></span>
          <span>•</span>
          <span>Prompt: <strong className="text-cyan-300 font-mono">{summary?.prompt_version || 'v1.0'}</strong></span>
        </div>
      </div>

      {/* Error Alert */}
      {(generateMutation.error || editMutation.error || acceptMutation.error || rejectMutation.error) && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Operation Alert: </span>
            {(generateMutation.error as any)?.message ||
             (editMutation.error as any)?.message ||
             (acceptMutation.error as any)?.message ||
             (rejectMutation.error as any)?.message}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {!summary && !isLoading && !generateMutation.isPending && (
        <div className="glass-panel p-12 rounded-2xl text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-400 flex items-center justify-center mx-auto">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">No Summary Generated Yet</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
              Click the 'Generate Summary' button above to synthesize structured dialogue and document extractions into a validated clinical summary.
            </p>
          </div>
          <button
            onClick={() => generateMutation.mutate()}
            className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-lg shadow-brand-500/20 transition-all"
          >
            Generate Clinical Summary Now
          </button>
        </div>
      )}

      {(isLoading || generateMutation.isPending) && (
        <div className="glass-panel p-12 rounded-2xl text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-brand-400 animate-spin mx-auto" />
          <p className="text-sm text-slate-300">Generating and validating clinical summary against Pydantic schema...</p>
        </div>
      )}

      {summary && (
        <div className="space-y-6">
          {/* AI vs Physician Edition Badge Bar */}
          <div className="flex items-center justify-between bg-slate-900/60 p-3 rounded-xl border border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              {isPhysicianEdited ? (
                <span className="px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-medium flex items-center gap-1">
                  <UserCheck className="w-3 h-3" /> Physician Edited Version
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-brand-500/15 border border-brand-500/30 text-brand-300 font-medium flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> AI Generated Base Version
                </span>
              )}
            </div>
            <span className="text-slate-400 font-mono">
              Version {summary.version} • Created: {new Date(summary.created_at).toLocaleTimeString()}
            </span>
          </div>

          {/* Narrative Summary Section */}
          <div className="glass-panel p-6 rounded-2xl space-y-3 border-l-4 border-brand-500">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-brand-400 flex items-center gap-2">
                <FileCheck className="w-4 h-4" /> Synthesized Narrative Summary
              </h3>
              {!isAccepted && !editing && (
                <button
                  onClick={() => {
                    setEditedText(activeSummary.generated_summary_text || '');
                    setEditing(true);
                  }}
                  className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 font-medium"
                >
                  <Edit3 className="w-3.5 h-3.5" /> Edit Narrative
                </button>
              )}
            </div>

            {editing ? (
              <div className="space-y-3">
                <textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  rows={4}
                  className="w-full p-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setEditing(false)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => editMutation.mutate(editedText)}
                    disabled={editMutation.isPending}
                    className="px-4 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-medium hover:bg-brand-500"
                  >
                    Save Narrative Edit
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-200 leading-relaxed">
                {activeSummary.generated_summary_text || 'No narrative text generated.'}
              </p>
            )}
          </div>

          {/* Preserved Red Flags */}
          {activeSummary.red_flags && activeSummary.red_flags.length > 0 && (
            <div className="glass-panel p-6 rounded-2xl space-y-3 border-l-4 border-rose-500">
              <h3 className="text-sm font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> Deterministic Red Flags Preserved
              </h3>
              <div className="space-y-2">
                {activeSummary.red_flags.map((flag: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/20 text-xs">
                    <span className="font-bold text-rose-300 block">{flag.flag_name}</span>
                    <span className="text-slate-300">{flag.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Structured Clinical Sections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Chief Complaint */}
            <div className="glass-panel p-5 rounded-2xl space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-brand-400">Chief Complaints</h4>
              {activeSummary.chief_complaint?.map((item: any, i: number) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs flex justify-between">
                  <span className="font-semibold text-white">{item.name}</span>
                  <span className="text-slate-400">{item.details}</span>
                </div>
              ))}
            </div>

            {/* History of Present Illness (HPI) */}
            <div className="glass-panel p-5 rounded-2xl space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-brand-400">History of Present Illness (HPI)</h4>
              {activeSummary.history_of_present_illness?.map((item: any, i: number) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs flex justify-between">
                  <span className="font-semibold text-slate-200">{item.name}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    item.status === 'DENIED' ? 'bg-rose-500/20 text-rose-300' : 'bg-brand-500/20 text-brand-300'
                  }`}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>

            {/* Current Medications & Allergies */}
            <div className="glass-panel p-5 rounded-2xl space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">Medications & Allergies</h4>
              {activeSummary.medications?.map((item: any, i: number) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs flex justify-between">
                  <span className="font-semibold text-slate-200">{item.name} ({item.dosage})</span>
                  <span className="text-slate-400">{item.frequency}</span>
                </div>
              ))}
            </div>

            {/* Lab Investigations */}
            <div className="glass-panel p-5 rounded-2xl space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Investigations & Labs</h4>
              {activeSummary.investigations?.map((item: any, i: number) => (
                <div key={i} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-white block">{item.test_name}</span>
                    <span className="text-slate-400 text-[10px]">Ref: {item.reference_range}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                    item.is_abnormal ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-300'
                  }`}>
                    {item.value} {item.is_abnormal ? '⚠️ ABNORMAL' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Explicit Information Gaps */}
          {activeSummary.information_gaps && activeSummary.information_gaps.length > 0 && (
            <div className="glass-panel p-5 rounded-2xl space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-slate-400" /> Explicit Information Gaps (Unknown / Not Provided)
              </h4>
              <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
                {activeSummary.information_gaps.map((gap: string, i: number) => (
                  <li key={i}>{gap}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Bar */}
          {!isAccepted && (
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <button
                onClick={() => setRejectModalOpen(true)}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 text-xs font-medium border border-rose-800/50 transition-colors"
              >
                <X className="w-4 h-4" />
                <span>Reject / Request Changes</span>
              </button>

              <button
                onClick={() => setNotesModalOpen(true)}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium shadow-lg shadow-brand-500/20 transition-all"
              >
                <Check className="w-4 h-4" />
                <span>Approve & Sign Summary</span>
              </button>
            </div>
          )}

          {/* Approved Info Banner */}
          {isAccepted && (
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
              <span className="flex items-center gap-2 font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Approved by Physician ({summary.accepted_by}) at {new Date(summary.accepted_at!).toLocaleString()}
              </span>
              {summary.physician_notes && (
                <span className="text-slate-400">Notes: "{summary.physician_notes}"</span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Reject Modal */}
      {rejectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel p-6 rounded-2xl max-w-md w-full space-y-4">
            <h3 className="text-base font-bold text-white">Reject Clinical Summary</h3>
            <p className="text-xs text-slate-400">Specify the reason for rejecting this summary (e.g. missing lab findings, incorrect history).</p>
            <textarea
              value={rejectReason}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setRejectReason(e.target.value)}
              rows={3}
              placeholder="Reason for rejection..."
              className="w-full p-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-rose-500"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setRejectModalOpen(false)} className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs">
                Cancel
              </button>
              <button
                onClick={() => rejectMutation.mutate()}
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                className="px-4 py-2 rounded-xl bg-rose-600 text-white text-xs font-semibold"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Accept Notes Modal */}
      {notesModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel p-6 rounded-2xl max-w-md w-full space-y-4">
            <h3 className="text-base font-bold text-white">Approve & Sign Summary</h3>
            <p className="text-xs text-slate-400">Optional physician review notes to attach to the official clinical summary.</p>
            <textarea
              value={physicianNotes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPhysicianNotes(e.target.value)}
              rows={3}
              placeholder="Physician notes (optional)..."
              className="w-full p-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-brand-500"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setNotesModalOpen(false)} className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs">
                Cancel
              </button>
              <button
                onClick={() => acceptMutation.mutate()}
                disabled={acceptMutation.isPending}
                className="px-4 py-2 rounded-xl bg-brand-600 text-white text-xs font-semibold"
              >
                Approve & Sign
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

