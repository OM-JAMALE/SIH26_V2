import React from 'react';
import { FileText, UploadCloud, CheckCircle, FileCheck } from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-brand-400" /> Medical Document Digitization
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Upload lab reports, prescriptions, or discharge summaries (PDF, PNG, JPEG).
          </p>
        </div>
        <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-mono">
          Module B — OCR & Vision Extraction
        </span>
      </div>

      {/* Upload Box */}
      <div className="glass-panel p-8 rounded-2xl border-2 border-dashed border-slate-700 hover:border-brand-500/50 text-center space-y-4 transition-colors">
        <div className="w-12 h-12 rounded-full bg-brand-500/10 text-brand-400 flex items-center justify-center mx-auto">
          <UploadCloud className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Drag and drop medical documents here, or click to browse</p>
          <p className="text-xs text-slate-400 mt-1">Supports PDF, PNG, JPEG (Max 10MB per file)</p>
        </div>
        <button className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors">
          Select Document File
        </button>
      </div>

      {/* Digitized Entities & Abnormalities Preview */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <FileCheck className="w-5 h-5 text-cyan-400" /> Extracted Entities & Lab Abnormality Rules
        </h3>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 text-center">
          No documents uploaded yet. Upload a lab report or prescription to extract structured entities.
        </div>
      </div>
    </div>
  );
};
