import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Stethoscope,
  Search,
  UserCheck,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ShieldAlert,
  ClipboardList,
  Sparkles,
  User,
  Activity,
  Edit3,
  Calendar,
  Check,
  X,
  FileCheck,
  ShieldCheck,
} from 'lucide-react';
import { searchPatientsForDoctor, fetchDoctorFullHistory } from '../api/client';
import { useToast } from '../components/common/Toast';

export const DoctorDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  const { data: searchResults, isLoading: isSearchLoading } = useQuery({
    queryKey: ['doctorPatientSearch', searchQuery],
    queryFn: () => searchPatientsForDoctor(searchQuery),
    enabled: searchQuery.length >= 2,
  });

  const { data: fullHistory, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['doctorFullHistory', selectedPatientId],
    queryFn: () => fetchDoctorFullHistory(selectedPatientId!),
    enabled: Boolean(selectedPatientId),
  });

  const handleSelectPatient = (ptId: string, ptName: string) => {
    setSelectedPatientId(ptId);
    toast.info(`Loaded clinical record for ${ptName}`, 'Patient Record Selected');
  };

  const handleReviewSummary = (sessionId: string) => {
    localStorage.setItem('active_session_id', sessionId);
    navigate(`/summary?session_id=${sessionId}`);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Doctor Portal Header Banner */}
      <div className="glass-panel-glow rounded-3xl p-6 sm:p-8 relative overflow-hidden border border-brand-500/20">
        <div className="absolute -right-10 -bottom-10 w-60 h-60 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium">
            <Stethoscope className="w-3.5 h-3.5 text-brand-400" />
            <span>Physician Portal & Clinical Review</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold font-heading text-white">
            Doctor Portal & Summary Sign-off
          </h1>
          <p className="text-sm text-slate-300 max-w-2xl">
            Search patient records by ABHA ID, Patient ID, or Phone Number to review pre-consultation histories, lab extractions, and sign off on clinical summaries.
          </p>
        </div>
      </div>

      {/* Patient Search Input Bar */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Patient Search & Record Lookup
        </h2>
        <form onSubmit={(e) => e.preventDefault()} className="relative">
          <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Type ABHA ID (e.g. 91-1234), Patient Name, Phone, or UUID..."
            className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-400"
          />
        </form>

        {/* Search Results List */}
        {isSearchLoading ? (
          <div className="text-xs text-slate-400 flex items-center gap-2 py-2">
            <Sparkles className="w-4 h-4 animate-spin text-brand-400" /> Searching patient registry...
          </div>
        ) : searchResults && searchResults.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
            {searchResults.map((pt: any) => (
              <div
                key={pt.id}
                onClick={() => handleSelectPatient(pt.id, `${pt.first_name} ${pt.last_name}`)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between group ${
                  selectedPatientId === pt.id
                    ? 'bg-brand-500/15 border-brand-500/50 shadow-glow-brand text-white'
                    : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800/60 text-slate-200'
                }`}
              >
                <div className="space-y-1">
                  <div className="font-bold text-sm text-white group-hover:text-brand-300 transition-colors">
                    {pt.first_name} {pt.last_name}
                  </div>
                  <div className="text-xs text-slate-400 font-mono flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-cyan-400" />
                    ABHA: {pt.national_health_id || 'Not Linked'}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Sessions: <strong className="text-slate-200">{pt.session_count}</strong> | Last: {pt.last_session_at ? new Date(pt.last_session_at).toLocaleDateString() : 'None'}
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-brand-400 group-hover:translate-x-1 transition-all" />
              </div>
            ))}
          </div>
        ) : searchQuery.length >= 2 ? (
          <div className="text-xs text-slate-400 py-2">No registered patients matching "{searchQuery}"</div>
        ) : (
          <div className="text-xs text-slate-400 py-1">
            Tip: Enter an ABHA ID (e.g., 91-1234) or Patient name to quickly view patient records.
          </div>
        )}
      </div>

      {/* Selected Patient Record Full View */}
      {selectedPatientId && (
        <div className="space-y-6">
          {isHistoryLoading ? (
            <div className="glass-card rounded-2xl p-8 text-center text-slate-400 text-sm">
              <Sparkles className="w-6 h-6 animate-spin text-brand-400 mx-auto mb-2" />
              Loading clinical record for doctor review...
            </div>
          ) : fullHistory ? (
            <div className="space-y-6">
              {/* Patient Banner */}
              <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <User className="w-5 h-5 text-brand-400" />
                    {fullHistory.patient.first_name} {fullHistory.patient.last_name}
                  </h2>
                  <div className="text-xs text-slate-400 space-x-3 mt-1">
                    <span>DOB: {fullHistory.patient.dob}</span>
                    <span>•</span>
                    <span>Gender: {fullHistory.patient.gender}</span>
                    <span>•</span>
                    <span className="font-mono text-cyan-300">ABHA: {fullHistory.patient.national_health_id || 'Unlinked'}</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300">
                    Total Sessions: <span className="font-bold text-white">{fullHistory.total_sessions}</span>
                  </div>
                  <div className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300">
                    Total Documents: <span className="font-bold text-white">{fullHistory.total_documents}</span>
                  </div>
                </div>
              </div>

              {/* Consultation Sessions List */}
              <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ClipboardList className="w-5 h-5 text-brand-400" />
                  Longitudinal Consultations & Summary Sign-off
                </h3>

                <div className="space-y-3">
                  {fullHistory.sessions.map((sess: any) => (
                    <div
                      key={sess.session_id}
                      className="p-5 rounded-xl bg-slate-900/60 hover:bg-slate-800/60 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-white">
                            {sess.chief_complaint || 'General Pre-consultation'}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono border border-slate-700">
                            Mode: {sess.mode}
                          </span>
                          <span className={`text-[10px] px-2.5 py-0.5 rounded font-bold ${
                            sess.summary_status === 'ACCEPTED'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : sess.summary_status === 'REJECTED'
                              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                              : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                          }`}>
                            Summary: {sess.summary_status}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 flex items-center gap-4">
                          <span>Date: {sess.created_at ? new Date(sess.created_at).toLocaleDateString() : 'N/A'}</span>
                          <span>•</span>
                          <span>Turns: {sess.turn_count}</span>
                          <span>•</span>
                          <span>Docs: {sess.document_count}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleReviewSummary(sess.session_id)}
                        className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md transition-all self-start md:self-auto flex items-center gap-2"
                      >
                        <Edit3 className="w-4 h-4" />
                        <span>Review & Sign Off</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
