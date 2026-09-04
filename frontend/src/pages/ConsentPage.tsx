import React from 'react';
import { ShieldCheck, FileCode, CheckCircle2, Lock } from 'lucide-react';

export const ConsentPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-brand-400" /> Consent Record & FHIR / ABDM Export
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Auditable consent logging and conversion to HL7 FHIR R4 Bundle standard.
          </p>
        </div>
        <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-mono">
          Module D — Consent & Adapter Isolation
        </span>
      </div>

      {/* Consent Record */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Lock className="w-5 h-5 text-emerald-400" /> Patient Explicit Consent
        </h3>

        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-400">Purpose:</span>
            <span className="font-semibold text-white">Pre-consultation clinical history synthesis and EHR integration</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Terms Version:</span>
            <span className="font-mono text-slate-300">v1.0 (India ABDM Compliant)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Status:</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Granted & Digitally Signed
            </span>
          </div>
        </div>
      </div>

      {/* FHIR Bundle Export Sandbox */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileCode className="w-5 h-5 text-cyan-400" /> FHIR R4 Clinical Document Bundle
          </h3>
          <button className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition-colors">
            Generate FHIR Bundle
          </button>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-cyan-300 overflow-x-auto">
          {`{
  "resourceType": "Bundle",
  "type": "document",
  "entry": [
    { "resource": { "resourceType": "Patient", "id": "demo-patient" } },
    { "resource": { "resourceType": "Composition", "status": "final", "title": "Clinical Summary Pre-Consultation" } }
  ]
}`}
        </div>
      </div>
    </div>
  );
};
