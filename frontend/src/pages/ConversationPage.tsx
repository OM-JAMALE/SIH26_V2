import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  MessageSquareHeart, 
  ShieldAlert, 
  Activity, 
  Send, 
  AlertTriangle, 
  CheckCircle2, 
  Lock, 
  RefreshCw, 
  Info,
  Shield,
  FileCheck,
  Stethoscope,
  Sparkles,
  ChevronRight,
  PhoneCall,
  Siren,
  ExternalLink
} from 'lucide-react';
import { 
  createSession, 
  getSessionState, 
  submitPatientResponse, 
  getConversationHistory, 
  acknowledgeDisclaimer,
  SessionStateData, 
  ConversationTurnData 
} from '../api/client';

// Must match exactly the backend ConversationSection enum values
const INTERVIEW_SECTIONS = [
  'CHIEF_COMPLAINT',
  'HPI',
  'SOCRATES',
  'PMH',
  'PSH',
  'DRUG_HISTORY',
  'ALLERGY_HISTORY',
  'FAMILY_HISTORY',
  'PERSONAL_HISTORY',
  'ROS',
  'COMPLETED'
];

export const ConversationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const paramSessionId = searchParams.get('session_id');
  const [sessionId, setSessionId] = useState<string>(
    paramSessionId || localStorage.getItem('active_session_id') || ''
  );

  const [session, setSession] = useState<SessionStateData | null>(null);
  const [history, setHistory] = useState<ConversationTurnData[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [acknowledging, setAcknowledging] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load or initialize session
  useEffect(() => {
    let isMounted = true;

    async function init() {
      setLoading(true);
      setError(null);

      let targetId = sessionId;
      if (!targetId) {
        try {
          const newSess = await createSession('patient-101', 'MODERN', false);
          targetId = newSess.session_id;
          localStorage.setItem('active_session_id', targetId);
          if (isMounted) setSessionId(targetId);
        } catch (e: any) {
          console.warn('Backend session creation failed, using client demo state:', e);
          targetId = 'demo-session-101';
          if (isMounted) setSessionId(targetId);
        }
      }

      try {
        const [sessData, historyData] = await Promise.all([
          getSessionState(targetId).catch(() => null),
          getConversationHistory(targetId).catch(() => []),
        ]);

        if (isMounted) {
          if (sessData) {
            setSession(sessData);
          } else {
            // Provide sensible demo state if backend session fetch fails
            setSession({
              session_id: targetId,
              patient_id: 'patient-101',
              lifecycle_status: 'IN_PROGRESS',
              mode: 'MODERN',
              disclaimer_acknowledged: false,
              current_section: 'CHIEF_COMPLAINT',
              latest_question: 'What is the main problem or symptom that brought you here today?',
              structured_history: {
                chief_complaint: [],
                hpi: {},
                medical_history: [],
                medications: [],
                allergies: [],
              },
              safety: { flagged: false },
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            });
          }

          if (historyData && historyData.length > 0) {
            setHistory(historyData);
          }
        }
      } catch (err: any) {
        if (isMounted) setError('Failed to connect to backend clinical engine');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    init();

    return () => {
      isMounted = false;
    };
  }, [sessionId]);

  // Scroll chat to bottom on updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, session?.latest_question]);

  // Handle disclaimer acknowledgement
  const handleAcknowledge = async () => {
    if (!sessionId) return;
    setAcknowledging(true);
    try {
      const updated = await acknowledgeDisclaimer(sessionId);
      setSession(updated);
    } catch (err: any) {
      console.warn('API acknowledge failed, setting state locally:', err);
      if (session) {
        setSession({ ...session, disclaimer_acknowledged: true });
      }
    } finally {
      setAcknowledging(false);
    }
  };

  // Handle response submission
  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || submitting || !session) return;

    const userText = inputText.trim();
    setInputText('');
    setSubmitting(true);
    setError(null);

    // Optimistically add user turn to history
    const tempPatientTurn: ConversationTurnData = {
      id: `temp-${Date.now()}`,
      session_id: session.session_id,
      turn_index: history.length + 1,
      speaker: 'PATIENT',
      content: userText,
      extracted_data: {},
      safety_alerts: {},
      section: session.current_section,
      created_at: new Date().toISOString(),
    };
    setHistory((prev) => [...prev, tempPatientTurn]);

    try {
      const result = await submitPatientResponse(session.session_id, userText);

      // Refresh session and full turn history
      const [updatedSess, updatedTurns] = await Promise.all([
        getSessionState(session.session_id).catch(() => null),
        getConversationHistory(session.session_id).catch(() => []),
      ]);

      if (updatedSess) {
        setSession(updatedSess);
      } else {
        setSession((prev) =>
          prev
            ? {
                ...prev,
                current_section: result.current_section,
                socrates_state: result.socrates_state,
                latest_question: result.next_question,
                lifecycle_status: result.lifecycle_status,
                safety: result.safety,
              }
            : null
        );
      }

      if (updatedTurns && updatedTurns.length > 0) {
        setHistory(updatedTurns);
      } else {
        // Add system response turn locally
        const sysTurn: ConversationTurnData = {
          id: `sys-${Date.now()}`,
          session_id: session.session_id,
          turn_index: history.length + 2,
          speaker: 'SYSTEM',
          content: result.next_question,
          extracted_data: result.structured_updates || {},
          safety_alerts: result.safety,
          section: result.current_section,
          created_at: new Date().toISOString(),
        };
        setHistory((prev) => [...prev, sysTurn]);
      }
    } catch (err: any) {
      console.error('Submit response failed:', err);
      const msg = err?.message || 'Error processing response. Please try again.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const isEscalated = session?.lifecycle_status === 'SAFETY_ESCALATED' || session?.safety?.flagged;
  const isCompleted = session?.lifecycle_status === 'COMPLETED' || session?.current_section === 'COMPLETED';

  const currentSectionIndex = INTERVIEW_SECTIONS.indexOf(session?.current_section || 'CHIEF_COMPLAINT');

  return (
    <div className="space-y-4 max-w-7xl mx-auto">
      {/* INITIAL CLINICAL DISCLAIMER MODAL */}
      {session && !session.disclaimer_acknowledged && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="glass-panel p-6 md:p-8 rounded-3xl max-w-lg w-full space-y-5 border border-brand-500/30 shadow-2xl">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/30">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Clinical Pre-Consultation Disclaimer</h3>
                <span className="text-xs text-amber-400 font-medium">Mandatory Patient Governance Acknowledgment</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3 text-xs text-slate-300 leading-relaxed">
              <p className="font-semibold text-slate-200">
                Important Information Regarding Your Session:
              </p>
              <p>
                This tool collects health information to help prepare for a consultation. It does not provide a medical diagnosis or replace a qualified healthcare professional. Do not rely on this system for emergency medical care.
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-400">
                <li>Non-diagnostic pre-consultation engine.</li>
                <li>Deterministic safety rules active for red-flag symptoms.</li>
                <li>Structured output subject to physician review and signature.</li>
              </ul>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={handleAcknowledge}
                disabled={acknowledging}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-semibold text-sm shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center space-x-2"
              >
                {acknowledging ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Shield className="w-4 h-4" />
                    <span>I Understand & Acknowledge</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DETERMINISTIC EMERGENCY ESCALATION MODAL */}
      {isEscalated && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-xl p-4 animate-fade-in">
          <div className="glass-panel p-6 md:p-8 rounded-3xl max-w-xl w-full space-y-6 border-2 border-rose-500 shadow-2xl shadow-rose-950/80 bg-slate-950/95 relative overflow-hidden">
            {/* Top Red Glow Accent Bar */}
            <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-rose-600 via-red-500 to-rose-600 animate-pulse" />

            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 border border-rose-500/40 animate-pulse">
                <Siren className="w-8 h-8 text-rose-500" />
              </div>
              <div>
                <h3 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
                  CRITICAL EMERGENCY ALERT
                  <span className="px-2 py-0.5 rounded-md bg-rose-500/30 text-rose-300 text-[10px] uppercase font-bold border border-rose-500/40">
                    Red Flag
                  </span>
                </h3>
                <p className="text-xs text-rose-400 font-medium mt-0.5">
                  Deterministic Safety Rules Triggered • Chat Input Locked
                </p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/30 space-y-2 text-xs text-rose-100 leading-relaxed">
              <div className="flex items-center space-x-2 text-rose-300 font-bold text-sm">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <span>Immediate Medical Evaluation Required</span>
              </div>
              <p className="text-slate-200">
                {session?.safety?.emergency_message ||
                  'Your reported symptoms indicate a potential medical emergency. The AI intake engine has stopped questioning so you can obtain immediate medical care.'}
              </p>
              {session?.safety?.rule_id && (
                <p className="text-[10px] text-rose-400 font-mono">
                  Triggered Safety Rule: {session.safety.rule_id}
                </p>
              )}
            </div>

            {/* Direct Call Trigger Buttons */}
            <div className="space-y-3 pt-1">
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Tap to Call Immediate Emergency Response Services:
              </label>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <a
                  href="tel:108"
                  className="py-4 px-5 rounded-2xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-bold text-sm shadow-xl shadow-rose-600/40 transition-all flex items-center justify-center space-x-3 border border-rose-400/30 group"
                >
                  <PhoneCall className="w-5 h-5 text-white animate-bounce" />
                  <div className="text-left">
                    <span className="block text-[10px] text-rose-200 font-normal uppercase">Ambulance / Emergency</span>
                    <span className="text-base tracking-wide">Call 108</span>
                  </div>
                </a>

                <a
                  href="tel:112"
                  className="py-4 px-5 rounded-2xl bg-slate-900 hover:bg-slate-800 text-rose-300 font-bold text-sm shadow-lg transition-all flex items-center justify-center space-x-3 border border-rose-500/40 group"
                >
                  <PhoneCall className="w-5 h-5 text-rose-400" />
                  <div className="text-left">
                    <span className="block text-[10px] text-slate-400 font-normal uppercase">National Helpline</span>
                    <span className="text-base tracking-wide">Call 112</span>
                  </div>
                </a>
              </div>

              <button
                onClick={() => window.open('https://maps.google.com/?q=nearest+hospital+emergency', '_blank')}
                className="w-full py-3 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 font-medium text-xs border border-slate-700 transition-all flex items-center justify-center space-x-2"
              >
                <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
                <span>Locate Nearest Hospital Emergency Room on Maps</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/20 text-brand-400 flex items-center justify-center border border-brand-500/30">
            <MessageSquareHeart className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Conversational Clinical Engine
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider ${
                session?.mode === 'AYUSH' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-brand-500/10 border-brand-500/30 text-brand-400'
              }`}>
                {session?.mode || 'MODERN'} MODE
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic Interview State Machine • Dynamic Extraction & Safety Rule Evaluation
            </p>
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400">Session ID:</span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-950 font-mono text-brand-300 border border-slate-800">
            {sessionId ? `${sessionId.substring(0, 18)}...` : 'Initializing...'}
          </span>
          <span className={`px-3 py-1 rounded-full font-bold uppercase tracking-wider text-[10px] border ${
            isEscalated
              ? 'bg-rose-500/20 border-rose-500/40 text-rose-300 animate-pulse'
              : isCompleted
              ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
              : 'bg-brand-500/15 border-brand-500/30 text-brand-300'
          }`}>
            {session?.lifecycle_status || 'IN_PROGRESS'}
          </span>
        </div>
      </div>

      {/* Progress Section Bar */}
      <div className="glass-panel p-3 rounded-2xl overflow-x-auto">
        <div className="flex items-center min-w-max space-x-2 text-xs">
          {INTERVIEW_SECTIONS.map((sec, idx) => {
            const isCurrent = session?.current_section === sec;
            const isPast = currentSectionIndex > idx;
            return (
              <React.Fragment key={sec}>
                <div
                  className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 font-medium transition-all ${
                    isCurrent
                      ? 'bg-brand-600 text-white font-bold shadow-md shadow-brand-500/20 border border-brand-400'
                      : isPast
                      ? 'bg-slate-800/80 text-emerald-400 border border-slate-700'
                      : 'bg-slate-900 text-slate-500 border border-slate-800'
                  }`}
                >
                  {isPast && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                  <span>{sec.replace('_', ' ')}</span>
                  {isCurrent && session?.socrates_state && (
                    <span className="px-1.5 py-0.5 rounded bg-brand-900 text-brand-200 text-[9px] font-mono">
                      {session.socrates_state}
                    </span>
                  )}
                </div>
                {idx < INTERVIEW_SECTIONS.length - 1 && (
                  <ChevronRight className="w-3 h-3 text-slate-600 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Chat Area + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dialogue Chat Container */}
        <div className="lg:col-span-2 space-y-4 flex flex-col h-[70vh]">
          {/* Messages Display Box */}
          <div className="flex-1 glass-panel rounded-2xl p-4 overflow-y-auto space-y-4 border border-slate-800/80">
            {/* Display Turn History */}
            {history.length === 0 && session?.latest_question && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md">
                  AI
                </div>
                <div className="glass-card p-4 rounded-2xl rounded-tl-none max-w-xl border border-brand-500/20">
                  <p className="text-sm text-slate-100 leading-relaxed">{session.latest_question}</p>
                  <span className="text-[10px] text-brand-400 mt-2 block font-medium">
                    Section: {session.current_section} {session.socrates_state ? `(${session.socrates_state})` : ''}
                  </span>
                </div>
              </div>
            )}

            {history.map((turn, index) => (
              <div
                key={turn.id || index}
                className={`flex items-start gap-3 ${turn.speaker === 'PATIENT' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md ${
                    turn.speaker === 'PATIENT'
                      ? 'bg-slate-700 text-slate-200'
                      : 'bg-brand-600 text-white'
                  }`}
                >
                  {turn.speaker === 'PATIENT' ? 'YOU' : 'AI'}
                </div>

                <div
                  className={`p-4 rounded-2xl max-w-xl text-sm leading-relaxed ${
                    turn.speaker === 'PATIENT'
                      ? 'bg-brand-500/20 border border-brand-500/30 text-white rounded-tr-none'
                      : 'glass-card text-slate-100 rounded-tl-none border border-slate-700/60'
                  }`}
                >
                  <p>{turn.content}</p>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-400">
                    <span>Section: {turn.section}</span>
                    <span>{new Date(turn.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              </div>
            ))}

            {/* Display latest system question if not present at end of history */}
            {history.length > 0 &&
              history[history.length - 1].speaker === 'PATIENT' &&
              session?.latest_question && (
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-md">
                    AI
                  </div>
                  <div className="glass-card p-4 rounded-2xl rounded-tl-none max-w-xl border border-brand-500/20">
                    <p className="text-sm text-slate-100 leading-relaxed">{session.latest_question}</p>
                    <span className="text-[10px] text-brand-400 mt-2 block font-medium">
                      Section: {session.current_section} {session.socrates_state ? `(${session.socrates_state})` : ''}
                    </span>
                  </div>
                </div>
              )}

            {/* AI Typing Indicator Skeleton */}
            {submitting && (
              <div className="flex items-start gap-3 animate-pulse">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-teal-400 flex items-center justify-center text-slate-950 text-xs font-bold shrink-0 shadow-md">
                  <Sparkles className="w-4 h-4 animate-spin text-slate-950" />
                </div>
                <div className="glass-card p-4 rounded-2xl rounded-tl-none max-w-xl border border-brand-500/30 space-y-2">
                  <div className="flex items-center gap-2 text-brand-300 text-xs font-semibold">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>AI Assistant is analyzing your response...</span>
                  </div>
                  <div className="h-2 w-56 bg-brand-500/20 rounded-full animate-pulse" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Emergency Safety Alert Banner inside Chat if Escalated */}
          {isEscalated && (
            <div className="p-4 rounded-2xl bg-rose-950/80 border-2 border-rose-500 text-rose-200 space-y-2 shadow-xl animate-pulse">
              <div className="flex items-center space-x-2 font-bold text-sm text-rose-300">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
                <span>Deterministic Emergency Red-Flag Escalation</span>
              </div>
              <p className="text-xs leading-relaxed font-semibold">
                {session?.safety?.emergency_message ||
                  'This may require urgent medical attention. This tool cannot assess or manage emergencies. Please seek immediate medical care or contact your local emergency service.'}
              </p>
              <div className="text-[10px] text-rose-400 pt-1 border-t border-rose-800/60 flex justify-between">
                <span>Rule ID: {session?.safety?.rule_id || 'RULE_SAFETY_ESCALATED'}</span>
                <span>Severity: {session?.safety?.severity || 'HIGH'}</span>
              </div>
            </div>
          )}

          {/* Input Box Form */}
          <form onSubmit={handleSubmit} className="glass-panel p-3 rounded-2xl flex items-center gap-2 border border-slate-800">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={submitting || isEscalated || isCompleted}
              placeholder={
                isEscalated
                  ? 'Interview locked due to safety escalation.'
                  : isCompleted
                  ? 'Interview section completed.'
                  : 'Type your response (e.g. I have sharp chest pain that started 2 hours ago...)'
              }
              className="flex-1 px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 text-sm disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={submitting || !inputText.trim() || isEscalated || isCompleted}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white text-sm font-semibold transition-all shadow-md shadow-brand-500/20 disabled:opacity-50 flex items-center space-x-2"
            >
              {submitting ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Send</span>
                  <Send className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
          {error && <p className="text-xs text-rose-400 px-2">{error}</p>}
        </div>

        {/* Sidebar: Live Extractions + Safety Governance */}
        <div className="space-y-4 overflow-y-auto max-h-[70vh]">
          {/* Live Structured Extractions Box */}
          <div className="glass-panel p-4 rounded-2xl space-y-3 border border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-2.5">
              <Activity className="w-4 h-4 text-cyan-400" /> Live Structured Extractions
            </h3>

            <div className="space-y-3 text-xs">
              {/* Chief Complaint */}
              {session?.structured_history?.chief_complaint?.length > 0 ? (
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                  <span className="text-brand-400 font-bold uppercase tracking-wider text-[10px] block">Chief Complaint</span>
                  {session?.structured_history?.chief_complaint?.map((item: any, i: number) => (
                    <div key={i} className="flex justify-between items-center text-slate-200">
                      <span className="font-semibold text-brand-200">{item.symptom || item.name}</span>
                      <span className="text-slate-400 text-[10px]">{item.duration}</span>
                    </div>
                  ))}
                </div>
              ) : null}

              {/* HPI / SOCRATES */}
              {session?.structured_history?.hpi && Object.keys(session.structured_history.hpi).length > 0 ? (
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                  <span className="text-cyan-400 font-bold uppercase tracking-wider text-[10px] block">HPI (SOCRATES)</span>
                  {Object.entries(session.structured_history.hpi).map(([k, v]: [string, any]) => (
                    <div key={k} className="flex justify-between text-slate-300">
                      <span className="capitalize text-slate-400">{k}:</span>
                      <span className="font-medium text-slate-100">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                    </div>
                  ))}
                </div>
              ) : null}

              {/* Past Medical History */}
              {session?.structured_history?.medical_history?.length > 0 ? (
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                  <span className="text-indigo-400 font-bold uppercase tracking-wider text-[10px] block">Medical History</span>
                  {session?.structured_history?.medical_history?.map((item: any, i: number) => (
                    <div key={i} className="flex justify-between items-center">
                      <span className="text-slate-200">{item.condition}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        item.status === 'DENIED' ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : null}

              {/* Medications & Allergies */}
              {session?.structured_history?.medications?.length > 0 || session?.structured_history?.allergies?.length > 0 ? (
                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                  <span className="text-emerald-400 font-bold uppercase tracking-wider text-[10px] block">Meds & Allergies</span>
                  {session?.structured_history?.medications?.map((item: any, i: number) => (
                    <div key={i} className="text-slate-300 flex justify-between">
                      <span>💊 {item.name}</span>
                      <span className="text-slate-400">{item.dosage}</span>
                    </div>
                  ))}
                  {session?.structured_history?.allergies?.map((item: any, i: number) => (
                    <div key={i} className="text-rose-300 flex justify-between">
                      <span>⚠️ {item.allergen}</span>
                      <span className="text-slate-400">{item.reaction}</span>
                    </div>
                  ))}
                </div>
              ) : null}

              {/* Empty state fallback */}
              {(!session?.structured_history ||
                (session.structured_history.chief_complaint?.length === 0 &&
                  !session.structured_history.hpi)) && (
                <p className="text-slate-500 text-xs text-center py-4">
                  Extracted facts will appear here live as patient responds.
                </p>
              )}
            </div>
          </div>

          {/* Safety Rule Status Component */}
          <div
            className={`glass-panel p-4 rounded-2xl space-y-3 border ${
              isEscalated
                ? 'border-rose-500 bg-rose-950/30'
                : 'border-emerald-500/30 bg-emerald-950/10'
            }`}
          >
            <h3 className="text-sm font-bold flex items-center gap-2">
              <ShieldAlert className={`w-4 h-4 ${isEscalated ? 'text-rose-400' : 'text-emerald-400'}`} />
              <span className={isEscalated ? 'text-rose-300' : 'text-emerald-300'}>
                Deterministic Safety Layer
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated on structured facts per turn. LLM does NOT diagnose or override red flags.
            </p>

            {isEscalated ? (
              <div className="p-3 rounded-xl bg-rose-900/40 border border-rose-500/40 text-xs text-rose-200 font-semibold space-y-1">
                <p>🚨 SAFETY ESCALATION TRIGGERED</p>
                <p className="text-[11px] font-normal text-rose-300">
                  {session?.safety?.emergency_message}
                </p>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>Standard pre-consultation flow. No critical emergency red-flags tripped.</span>
              </div>
            )}
          </div>

          {/* Persistent Disclaimer Box */}
          <div className="glass-card p-4 rounded-2xl text-[11px] text-slate-400 border border-slate-800 space-y-1">
            <span className="font-bold text-slate-300 block flex items-center gap-1">
              <Info className="w-3.5 h-3.5 text-brand-400" /> Pre-Consultation Information Boundary
            </span>
            <p>
              This engine collects clinical history for physician review. It does not provide medical diagnoses or treatment recommendations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
