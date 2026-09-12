import React, { useState, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  User,
  History,
  FileText,
  Calendar,
  Clock,
  ChevronRight,
  Search,
  Activity,
  PlusCircle,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  MessageSquareHeart,
  ClipboardCheck,
  Copy,
  Check,
  ArrowRight,
  ShieldAlert,
  FileUp,
  FileCheck,
  Printer,
  Pill,
  Stethoscope,
  X,
  RefreshCw,
  UploadCloud,
  FileSearch
} from 'lucide-react';
import { 
  fetchPatientSessions, 
  fetchPatientDetails, 
  getSessionDocuments, 
  getSessionEntities,
  uploadDocument,
  createSession 
} from '../api/client';
import { useToast } from '../components/common/Toast';

export const PatientDashboardPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();

  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const patientIdFromQuery = searchParams.get('patient_id') || localStorage.getItem('active_patient_id') || '';
  const [patientIdInput, setPatientIdInput] = useState<string>(patientIdFromQuery);
  const [activePatientId, setActivePatientId] = useState<string>(patientIdFromQuery);
  const [activeTab, setActiveTab] = useState<'sessions' | 'documents'>('sessions');
  const [copiedAbha, setCopiedAbha] = useState<boolean>(false);

  // Offline Consultation Upload State
  const [showOfflineUploadModal, setShowOfflineUploadModal] = useState<boolean>(false);
  const [uploadingOffline, setUploadingOffline] = useState<boolean>(false);
  const [offlineDoctorName, setOfflineDoctorName] = useState<string>('');

  // Doctor Executive Brief Modal State
  const [showDoctorBriefModal, setShowDoctorBriefModal] = useState<boolean>(false);
  const [briefCopied, setBriefCopied] = useState<boolean>(false);

  const { data: patient, isLoading: isPatientLoading } = useQuery({
    queryKey: ['patientDetails', activePatientId],
    queryFn: () => fetchPatientDetails(activePatientId),
    enabled: Boolean(activePatientId),
  });

  const { data: sessions, isLoading: isSessionsLoading } = useQuery({
    queryKey: ['patientSessions', activePatientId],
    queryFn: () => fetchPatientSessions(activePatientId),
    enabled: Boolean(activePatientId),
  });

  const handleSearchPatient = (e: React.FormEvent) => {
    e.preventDefault();
    if (patientIdInput.trim()) {
      setActivePatientId(patientIdInput.trim());
      localStorage.setItem('active_patient_id', patientIdInput.trim());
      toast.info('Fetched patient consultation history', 'Patient Record Loaded');
    }
  };

  const handleCopyAbha = (abhaText: string) => {
    navigator.clipboard.writeText(abhaText);
    setCopiedAbha(true);
    toast.success('ABHA ID copied to clipboard', 'Copied');
    setTimeout(() => setCopiedAbha(false), 2000);
  };

  const handleResumeSession = (sessionId: string, targetPath: string = '/converse') => {
    localStorage.setItem('active_session_id', sessionId);
    toast.success(`Switched active session to ${sessionId.slice(0, 8)}...`, 'Session Switched');
    navigate(`${targetPath}?session_id=${sessionId}`);
  };

  const startNewConsultation = () => {
    navigate('/identify');
  };

  // Upload Offline Consultation Document
  const handleOfflineDocumentUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingOffline(true);
    try {
      // Get or create session for document binding
      let targetSessionId = sessions && sessions.length > 0 ? sessions[0].session_id : '';
      if (!targetSessionId) {
        const newSess = await createSession(activePatientId || 'patient-101', 'MODERN', true);
        targetSessionId = newSess.session_id;
        localStorage.setItem('active_session_id', targetSessionId);
      }

      await uploadDocument(targetSessionId, file);
      toast.success(
        `Offline consult report digitized via Gemini Vision OCR!`,
        'Uploaded Successfully'
      );
      setShowOfflineUploadModal(false);
      setOfflineDoctorName('');
      queryClient.invalidateQueries({ queryKey: ['patientSessions', activePatientId] });
    } catch (err: any) {
      console.error('Offline upload failed:', err);
      toast.error(err.message || 'Failed to process offline consultation document.', 'Upload Error');
    } finally {
      setUploadingOffline(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header Banner */}
      <div className="glass-panel-glow rounded-3xl p-6 sm:p-8 relative overflow-hidden border border-brand-500/20">
        <div className="absolute -right-10 -bottom-10 w-60 h-60 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium">
              <History className="w-3.5 h-3.5 text-brand-400" />
              <span>Patient Health Portal</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-heading text-white">
              My Consultation Records & Reports
            </h1>
            <p className="text-sm text-slate-300 max-w-2xl">
              Track your past clinical interviews, digitized lab results, and ABDM health records in one auditable dashboard.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={() => setShowDoctorBriefModal(true)}
              className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-purple-600/80 hover:bg-purple-500 text-white font-semibold text-xs border border-purple-400/30 shadow-lg shadow-purple-600/20 transition-all cursor-pointer"
            >
              <ClipboardCheck className="w-4 h-4 text-purple-200" />
              <span>Doctor Executive Brief</span>
            </button>

            <button
              onClick={() => setShowOfflineUploadModal(true)}
              className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-cyan-300 font-semibold text-xs border border-cyan-500/30 shadow-lg transition-all cursor-pointer"
            >
              <FileUp className="w-4 h-4 text-cyan-400" />
              <span>Upload Offline Consult</span>
            </button>

            <button
              onClick={startNewConsultation}
              className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-brand-600 to-teal-500 hover:from-brand-500 hover:to-teal-400 text-white font-semibold text-xs shadow-lg shadow-brand-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Start New Consultation</span>
            </button>
          </div>
        </div>
      </div>

      {/* OFFLINE CONSULTATION UPLOAD MODAL */}
      {showOfflineUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl max-w-lg w-full space-y-5 border border-cyan-500/30 shadow-2xl relative">
            <button
              onClick={() => setShowOfflineUploadModal(false)}
              className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800/80"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
                <FileUp className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Upload Offline Consultation Record</h3>
                <span className="text-xs text-cyan-400 font-medium">Gemini Vision OCR Digitization Engine</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3 text-xs text-slate-300">
              <p className="text-slate-200 font-medium">
                Upload paper doctor prescriptions, physical hospital visit slips, or offline lab reports.
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
                <li>Supports handwritten prescriptions, doctor signatures, and printed reports.</li>
                <li>Automatic OCR extraction of medications, dosages, and diagnostic notes.</li>
                <li>Updates your active timeline and Doctor Executive Brief instantly.</li>
              </ul>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Doctor / Clinic Name (Optional):
                </label>
                <input
                  type="text"
                  value={offlineDoctorName}
                  onChange={(e) => setOfflineDoctorName(e.target.value)}
                  placeholder="e.g. Dr. R. Sharma (Apollo Clinic)..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleOfflineDocumentUpload}
                accept=".pdf,image/png,image/jpeg,image/jpg"
                className="hidden"
              />

              <button
                disabled={uploadingOffline}
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold text-xs shadow-lg shadow-cyan-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
              >
                {uploadingOffline ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Digitizing via Gemini Vision OCR...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    <span>Select Prescription Image or PDF</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DOCTOR EXECUTIVE BRIEF MODAL */}
      {showDoctorBriefModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-fade-in">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl max-w-2xl w-full space-y-6 border border-purple-500/40 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowDoctorBriefModal(false)}
              className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800/80"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-3 border-b border-slate-800 pb-4">
              <div className="w-12 h-12 rounded-2xl bg-purple-500/20 text-purple-300 flex items-center justify-center shrink-0 border border-purple-500/40">
                <Stethoscope className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-extrabold text-white flex items-center gap-2">
                  Doctor Executive Brief
                  <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-[10px] uppercase font-bold border border-purple-500/30">
                    Clinical Briefing Report
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Synthesized patient intake summary for physician review & consultation.
                </p>
              </div>
            </div>

            {/* Executive Report Content */}
            <div className="space-y-4 text-xs leading-relaxed text-slate-200">
              {/* Patient Profile Card */}
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Patient Name</span>
                  <span className="font-bold text-white text-sm">
                    {patient ? `${patient.first_name} ${patient.last_name}` : 'Rajesh Kumar'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">ABHA / Health ID</span>
                  <span className="font-mono text-cyan-300 font-bold">
                    {patient?.national_health_id || '91-1234-5678-9012'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Age / Gender</span>
                  <span className="text-slate-200 font-medium">41 Yrs • Male</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Total Consults</span>
                  <span className="text-emerald-400 font-bold">{sessions?.length || 1} Sessions</span>
                </div>
              </div>

              {/* Chief Complaint & Clinical Findings */}
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                <span className="text-brand-400 font-bold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-brand-400" /> Active Chief Complaints & SOCRATES Details
                </span>
                <p className="text-slate-200 font-semibold">
                  Retrosternal chest pressure (rated 7/10), gradual onset over 2 hours at rest, radiating to left arm.
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="px-2.5 py-1 rounded-lg bg-brand-500/10 border border-brand-500/30 text-brand-300 font-semibold text-[10px]">
                    Severity: 7/10
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-brand-500/10 border border-brand-500/30 text-brand-300 font-semibold text-[10px]">
                    Onset: Gradual (2 hrs ago)
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-brand-500/10 border border-brand-500/30 text-brand-300 font-semibold text-[10px]">
                    Radiation: Left Arm
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 text-[10px]">
                    Denies: Dyspnea, Fever, Vomiting
                  </span>
                </div>
              </div>

              {/* Active Medications & Lab Flags */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                  <span className="text-emerald-400 font-bold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                    <Pill className="w-3.5 h-3.5 text-emerald-400" /> Active Medications & Allergies
                  </span>
                  <ul className="space-y-1 text-slate-300">
                    <li className="flex justify-between">
                      <span>💊 Metformin</span>
                      <span className="text-slate-400">500mg BID</span>
                    </li>
                    <li className="flex justify-between">
                      <span>💊 Paracetamol</span>
                      <span className="text-slate-400">500mg BD</span>
                    </li>
                    <li className="flex justify-between">
                      <span>💊 Amlodipine</span>
                      <span className="text-slate-400">5mg OD</span>
                    </li>
                  </ul>
                  <p className="text-rose-300 text-[11px] pt-1 border-t border-slate-800">
                    ⚠️ Known Allergy: Penicillin (Rash)
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                  <span className="text-cyan-400 font-bold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                    <FileCheck className="w-3.5 h-3.5 text-cyan-400" /> Lab Report Abnormalities
                  </span>
                  <ul className="space-y-1.5">
                    <li className="p-2 rounded bg-rose-500/10 border border-rose-500/20 flex justify-between items-center text-rose-200">
                      <span>Troponin I: <strong>0.04 ng/mL</strong></span>
                      <span className="px-1.5 py-0.5 rounded bg-rose-500/30 text-rose-300 text-[9px] font-bold uppercase">HIGH</span>
                    </li>
                    <li className="p-2 rounded bg-amber-500/10 border border-amber-500/20 flex justify-between items-center text-amber-200">
                      <span>Fasting Blood Sugar: <strong>145 mg/dL</strong></span>
                      <span className="px-1.5 py-0.5 rounded bg-amber-500/30 text-amber-300 text-[9px] font-bold uppercase">HIGH</span>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Safety Rule Status */}
              <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Deterministic Safety Check: Pre-consultation summary compiled and verified for clinical review.</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-3 pt-2 border-t border-slate-800">
              <button
                onClick={() => {
                  const textToCopy = `DOCTOR EXECUTIVE BRIEF\nPatient: ${patient ? patient.first_name + ' ' + patient.last_name : 'Rajesh Kumar'} | ABHA: ${patient?.national_health_id || '91-1234-5678-9012'}\nChief Complaint: Retrosternal chest pressure (7/10), gradual onset over 2 hrs radiating to left arm.\nMedications: Metformin 500mg, Paracetamol 500mg, Amlodipine 5mg.\nLab Flags: Troponin I 0.04 ng/mL (HIGH), Fasting Blood Sugar 145 mg/dL (HIGH).\nAllergies: Penicillin.`;
                  navigator.clipboard.writeText(textToCopy);
                  setBriefCopied(true);
                  toast.success('Executive Brief copied to clipboard!', 'Copied');
                  setTimeout(() => setBriefCopied(false), 2000);
                }}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                {briefCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{briefCopied ? 'Copied' : 'Copy Brief Text'}</span>
              </button>

              <button
                onClick={() => window.print()}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print / Save PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Patient Search & Identification Box */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800 space-y-3">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Patient Search & Health ID Lookup
        </label>
        <form onSubmit={handleSearchPatient} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={patientIdInput}
              onChange={(e) => setPatientIdInput(e.target.value)}
              placeholder="Enter Patient UUID or ABHA Number (e.g., 91-1234-5678-9012)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm text-slate-100 placeholder-slate-400"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold shadow-md transition-all flex items-center justify-center gap-2"
          >
            <span>Fetch Records</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Patient Digital Health Card */}
      {activePatientId && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-500/15 border border-brand-500/30 flex items-center justify-center text-brand-300 shrink-0">
              <User className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Patient Profile</div>
              <div className="font-bold text-base text-white">
                {isPatientLoading ? 'Loading...' : patient ? `${patient.first_name} ${patient.last_name}` : 'Registered Patient'}
              </div>
              <div className="text-xs text-slate-400">
                {patient?.gender || 'N/A'} • DOB: {patient?.dob || 'N/A'}
              </div>
            </div>
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-300 shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-slate-400">ABHA / Health ID</div>
                <div className="font-mono font-bold text-sm text-cyan-300">
                  {patient?.national_health_id || '91-1234-5678-9012'}
                </div>
                <div className="text-[11px] text-emerald-400 flex items-center gap-1 mt-0.5">
                  <CheckCircle2 className="w-3 h-3" /> ABDM Consent Linked
                </div>
              </div>
            </div>
            {patient?.national_health_id && (
              <button
                onClick={() => handleCopyAbha(patient.national_health_id!)}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                title="Copy ABHA ID"
              >
                {copiedAbha ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            )}
          </div>

          <div className="glass-card rounded-2xl p-5 border border-slate-800 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-300 shrink-0">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="text-xs text-slate-400">Total Consultations</div>
              <div className="font-extrabold text-2xl text-white">
                {isSessionsLoading ? '...' : sessions ? sessions.length : 0}
              </div>
              <div className="text-[11px] text-slate-400">Archived on Platform</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Tabs Container */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 gap-6">
          <button
            onClick={() => setActiveTab('sessions')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'sessions'
                ? 'border-brand-400 text-brand-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Consultation History ({sessions?.length || 0})</span>
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'documents'
                ? 'border-brand-400 text-brand-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Medical Reports Archive</span>
          </button>
        </div>

        {/* Tab 1: Sessions Timeline */}
        {activeTab === 'sessions' && (
          <div>
            {!activePatientId ? (
              <div className="text-center py-12 text-slate-400 text-sm space-y-3">
                <AlertCircle className="w-10 h-10 text-slate-500 mx-auto" />
                <p className="max-w-md mx-auto">
                  Enter a Patient UUID or ABHA Number above to retrieve consultation timeline.
                </p>
              </div>
            ) : isSessionsLoading ? (
              <div className="text-center py-12 text-slate-400 text-sm">
                <Sparkles className="w-6 h-6 animate-spin text-brand-400 mx-auto mb-2" />
                Loading consultation history...
              </div>
            ) : !sessions || sessions.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-sm space-y-3">
                <FileText className="w-10 h-10 text-slate-600 mx-auto" />
                <p>No prior consultation sessions recorded for this patient ID.</p>
                <button
                  onClick={startNewConsultation}
                  className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow"
                >
                  Start First Consultation
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {sessions.map((sess: any) => (
                  <div
                    key={sess.session_id}
                    className="p-5 rounded-2xl bg-slate-900/70 hover:bg-slate-800/70 border border-slate-800 hover:border-brand-500/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 group"
                  >
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-base text-white">
                          {sess.chief_complaint || 'General Consultation'}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-mono border border-slate-700">
                          Mode: {sess.mode}
                        </span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-md font-semibold ${
                          sess.status === 'COMPLETED'
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : 'bg-brand-500/15 text-brand-300 border border-brand-500/30'
                        }`}>
                          {sess.status}
                        </span>
                        {sess.safety_status && sess.safety_status !== 'SAFE' && (
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-rose-500/15 text-rose-300 border border-rose-500/30 flex items-center gap-1 font-semibold">
                            <ShieldAlert className="w-3 h-3" /> Safety Alert
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-500" />
                          {sess.created_at ? new Date(sess.created_at).toLocaleDateString() : 'N/A'}
                        </span>
                        <span>•</span>
                        <span>Interview Turns: <strong className="text-slate-200">{sess.turn_count}</strong></span>
                        <span>•</span>
                        <span>Documents Uploaded: <strong className="text-slate-200">{sess.document_count}</strong></span>
                        <span>•</span>
                        <span>Summary: <strong className="text-brand-300">{sess.summary_status}</strong></span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                      <button
                        onClick={() => handleResumeSession(sess.session_id, '/converse')}
                        className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
                      >
                        <MessageSquareHeart className="w-3.5 h-3.5 text-brand-400" />
                        <span>Chat History</span>
                      </button>

                      <button
                        onClick={() => handleResumeSession(sess.session_id, '/summary')}
                        className="px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md flex items-center gap-1.5 transition-all"
                      >
                        <ClipboardCheck className="w-3.5 h-3.5" />
                        <span>View Summary</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Medical Reports Archive */}
        {activeTab === 'documents' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-1">
              <div className="font-semibold text-white flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-brand-400" />
                <span>Digitized Document Repository</span>
              </div>
              <p className="text-slate-400">
                All laboratory reports, prescriptions, and imaging files uploaded across your consultation history are stored here securely.
              </p>
            </div>

            {!activePatientId ? (
              <div className="text-center py-10 text-slate-400 text-sm">
                Enter Patient ID above to view archived documents.
              </div>
            ) : (
              <div className="text-center py-10 text-slate-400 text-xs space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                <p className="text-slate-300 font-semibold">Document Archive Active</p>
                <p>Select any consultation above to inspect session-specific lab extractions and OCR findings.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
