import React, { useState } from 'react';
import { UserCheck, ShieldAlert, ArrowRight, Stethoscope, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { createSession } from '../api/client';

export const PatientPage: React.FC = () => {
  const navigate = useNavigate();
  const [patientId, setPatientId] = useState<string>('patient-101');
  const [patientName, setPatientName] = useState<string>('Rajesh Kumar');
  const [mode, setMode] = useState<'MODERN' | 'AYUSH'>('MODERN');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const session = await createSession(patientId || 'patient-101', mode, false);
      localStorage.setItem('active_session_id', session.session_id);
      navigate(`/converse?session_id=${session.session_id}`);
    } catch (err: any) {
      console.error('Failed to create session:', err);
      setError(err.message || 'Failed to connect to backend server. Please verify the backend API is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-brand-400" /> Patient Identification & Intake
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Lookup patient via ABHA (National Health ID) and select interview system mode.
          </p>
        </div>
        <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-mono">
          Module A Identification
        </span>
      </div>

      <div className="glass-panel p-6 rounded-2xl space-y-6">
        {/* Mode Selector (MODERN vs AYUSH) */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
            Clinical System Mode
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setMode('MODERN')}
              className={`p-4 rounded-xl border flex items-start gap-3 text-left transition-all ${
                mode === 'MODERN'
                  ? 'bg-brand-500/15 border-brand-500 text-white shadow-lg shadow-brand-500/10'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Stethoscope className={`w-5 h-5 mt-0.5 shrink-0 ${mode === 'MODERN' ? 'text-brand-400' : 'text-slate-500'}`} />
              <div>
                <span className="font-bold text-sm block">Modern Medicine Flow</span>
                <span className="text-xs text-slate-400 mt-0.5 block">
                  Standard evidence-based clinical history taking (SOCRATES, HPI, ROS, PMH).
                </span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setMode('AYUSH')}
              className={`p-4 rounded-xl border flex items-start gap-3 text-left transition-all ${
                mode === 'AYUSH'
                  ? 'bg-cyan-500/15 border-cyan-500 text-white shadow-lg shadow-cyan-500/10'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <Sparkles className={`w-5 h-5 mt-0.5 shrink-0 ${mode === 'AYUSH' ? 'text-cyan-400' : 'text-slate-500'}`} />
              <div>
                <span className="font-bold text-sm block">AYUSH Intake Flow</span>
                <span className="text-xs text-slate-400 mt-0.5 block">
                  Traditional holistic history templates isolated from modern medicine assumptions.
                </span>
              </div>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              National Health ID / ABHA Number
            </label>
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="e.g. patient-101"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              placeholder="e.g. Rajesh Kumar"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-brand-950/40 border border-brand-500/20 text-xs text-brand-300 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-brand-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-brand-200">Patient Privacy & Governance</p>
            <p className="text-slate-400 mt-0.5">
              All pre-consultation intake data is audited, encrypted, and governed by explicit initial disclaimers.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300">
            {error}
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={handleStartSession}
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-medium shadow-lg shadow-brand-500/25 transition-all disabled:opacity-50"
          >
            <span>{loading ? 'Initializing Session...' : 'Start Pre-Consultation Session'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

