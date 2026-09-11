import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  FileText, 
  UploadCloud, 
  CheckCircle2, 
  FileCheck, 
  AlertTriangle, 
  Trash2, 
  Filter, 
  Activity, 
  File, 
  Image, 
  AlertCircle, 
  RefreshCw,
  Sparkles,
  Pill,
  HeartPulse,
  Stethoscope,
  Info
} from 'lucide-react';
import { 
  createSession,
  uploadDocument, 
  getSessionDocuments, 
  getSessionEntities, 
  deleteDocument,
  DocumentData, 
  ExtractedEntityData 
} from '../api/client';

export const DocumentsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const paramSessionId = searchParams.get('session_id');
  const [sessionId, setSessionId] = useState<string>(
    paramSessionId || localStorage.getItem('active_session_id') || ''
  );

  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [entities, setEntities] = useState<ExtractedEntityData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [abnormalOnly, setAbnormalOnly] = useState<boolean>(false);

  // Fetch documents and entities
  const loadData = async (sessId: string) => {
    if (!sessId) return;
    setLoading(true);
    setError(null);
    try {
      const [docsData, entitiesData] = await Promise.all([
        getSessionDocuments(sessId).catch(() => []),
        getSessionEntities(sessId, false).catch(() => ({ entities: [], total: 0, abnormal_count: 0 })),
      ]);
      setDocuments(docsData || []);
      setEntities(entitiesData.entities || []);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function initSession() {
      let targetId = paramSessionId || sessionId;
      if (!targetId || targetId === 'demo-session-uuid-101') {
        const stored = localStorage.getItem('active_session_id');
        if (stored && stored !== 'demo-session-uuid-101') {
          targetId = stored;
        } else {
          try {
            const newSess = await createSession('patient-101', 'MODERN', true);
            targetId = newSess.session_id;
            localStorage.setItem('active_session_id', targetId);
          } catch (e) {
            console.warn('Auto-session creation failed:', e);
            targetId = 'demo-session-uuid-101';
          }
        }
      }
      if (isMounted) {
        setSessionId(targetId);
        loadData(targetId);
      }
    }
    initSession();
    return () => { isMounted = false; };
  }, [paramSessionId]);

  const handleFileUpload = async (file: File) => {
    if (!file) return;

    // Client-side file type validation
    const validMimes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    const validExts = ['.pdf', '.png', '.jpg', '.jpeg'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validMimes.includes(file.type) && !validExts.includes(ext)) {
      setError('Invalid file type. Please upload a PDF, PNG, or JPEG medical document.');
      return;
    }

    // Client-side size validation (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10MB limit.');
      return;
    }

    setUploading(true);
    setError(null);
    try {
      // Ensure target session is valid in DB
      let targetId = sessionId;
      if (!targetId || targetId === 'demo-session-uuid-101') {
        const newSess = await createSession('patient-101', 'MODERN', true);
        targetId = newSess.session_id;
        localStorage.setItem('active_session_id', targetId);
        setSessionId(targetId);
      }

      await uploadDocument(targetId, file);
      // Reload documents and extracted entities
      await loadData(targetId);
    } catch (err: any) {
      console.error('Upload failed:', err);
      setError(err.message || 'Failed to upload and digitize medical document.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this document and its extracted clinical entities?')) {
      return;
    }
    try {
      await deleteDocument(sessionId, docId);
      await loadData(sessionId);
    } catch (err: any) {
      console.error('Delete failed:', err);
      setError(err.message || 'Failed to delete document.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const filteredEntities = entities.filter((e) => {
    if (abnormalOnly && !e.is_abnormal) return false;
    if (filterType !== 'ALL' && e.entity_type !== filterType) return false;
    return true;
  });

  const abnormalEntitiesCount = entities.filter((e) => e.is_abnormal).length;

  const getEntityIcon = (type: string) => {
    switch (type) {
      case 'LAB_RESULT':
        return <Activity className="w-4 h-4 text-cyan-400" />;
      case 'MEDICATION':
        return <Pill className="w-4 h-4 text-emerald-400" />;
      case 'DIAGNOSIS':
        return <Stethoscope className="w-4 h-4 text-purple-400" />;
      case 'VITAL':
        return <HeartPulse className="w-4 h-4 text-amber-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-brand-400" /> Medical Document Digitization
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Automated OCR, schema-validated structured entity extraction, and deterministic lab abnormality detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-mono">
            Module B — Document Engine
          </span>
          <button
            onClick={() => loadData(sessionId)}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Document Processing Alert: </span>
            {error}
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200">
            &times;
          </button>
        </div>
      )}

      {/* Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`glass-panel p-8 rounded-2xl border-2 border-dashed text-center space-y-4 transition-all ${
          isDragging
            ? 'border-brand-400 bg-brand-500/10 scale-[1.01]'
            : 'border-slate-700 hover:border-brand-500/50'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileUpload(e.target.files[0]);
            }
          }}
          accept=".pdf,image/png,image/jpeg,image/jpg"
          className="hidden"
        />

        <div className="w-14 h-14 rounded-2xl bg-brand-500/10 text-brand-400 flex items-center justify-center mx-auto shadow-inner">
          {uploading ? (
            <RefreshCw className="w-7 h-7 animate-spin text-brand-400" />
          ) : (
            <UploadCloud className="w-7 h-7" />
          )}
        </div>

        <div>
          <p className="text-base font-semibold text-white">
            {uploading ? 'Digitizing & Extracting Clinical Data...' : 'Drop medical reports here, or browse from computer'}
          </p>
          <p className="text-xs text-slate-400 mt-1.5">
            Supported formats: <strong className="text-slate-300">PDF, PNG, JPEG</strong> (Up to 10MB per document)
          </p>
        </div>

        <button
          type="button"
          disabled={uploading}
          onClick={() => fileInputRef.current?.click()}
          className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-brand-600/20 transition-all cursor-pointer"
        >
          {uploading ? 'Processing Extraction...' : 'Select Document File'}
        </button>
      </div>

      {/* Uploaded Documents List */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <File className="w-5 h-5 text-brand-400" /> Uploaded Documents ({documents.length})
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            Session: {sessionId.substring(0, 8)}...
          </span>
        </div>

        {documents.length === 0 ? (
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 text-center">
            No medical documents uploaded yet. Upload a lab report, prescription, or scan above to begin digitization.
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const isPdf = doc.mime_type.includes('pdf');
              return (
                <div
                  key={doc.id}
                  className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between gap-4 hover:border-slate-700 transition-all"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shrink-0">
                      {isPdf ? (
                        <FileText className="w-5 h-5 text-red-400" />
                      ) : (
                        <Image className="w-5 h-5 text-cyan-400" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="font-semibold text-xs text-white truncate">{doc.filename}</div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                        <span>{formatFileSize(doc.file_size)}</span>
                        <span>•</span>
                        <span>{new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${
                        doc.processing_status === 'EXTRACTED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : doc.processing_status === 'PENDING'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {doc.processing_status === 'EXTRACTED' && <CheckCircle2 className="w-3 h-3" />}
                      {doc.processing_status === 'PENDING' && <RefreshCw className="w-3 h-3 animate-spin" />}
                      {doc.processing_status === 'FAILED' && <AlertTriangle className="w-3 h-3" />}
                      {doc.processing_status}
                    </span>

                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Delete Document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Extracted Clinical Entities & Deterministic Lab Rules */}
      <div className="glass-panel p-6 rounded-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-cyan-400" /> Extracted Entities & Lab Reference Rules
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Numerical lab abnormalities are calculated deterministically against explicit physiological reference ranges.
            </p>
          </div>

          {/* Quick Metrics Badges */}
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold">
              Total: {entities.length}
            </span>
            {abnormalEntitiesCount > 0 && (
              <span className="px-3 py-1 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" /> {abnormalEntitiesCount} Abnormal
              </span>
            )}
          </div>
        </div>

        {/* Filters and Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800">
          <div className="flex flex-wrap items-center gap-2">
            {['ALL', 'LAB_RESULT', 'MEDICATION', 'DIAGNOSIS', 'VITAL'].map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  filterType === type
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {type === 'ALL' ? 'All Findings' : type.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            onClick={() => setAbnormalOnly(!abnormalOnly)}
            className={`px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
              abnormalOnly
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            {abnormalOnly ? 'Showing Abnormal Only' : 'Filter Abnormal Only'}
          </button>
        </div>

        {/* Entities Grid */}
        {filteredEntities.length === 0 ? (
          <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center space-y-2">
            <Info className="w-6 h-6 text-slate-500 mx-auto" />
            <p className="text-xs text-slate-400">
              {entities.length === 0
                ? 'No structured entities extracted yet. Upload medical documents above.'
                : 'No entities match the selected filter criteria.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredEntities.map((entity) => (
              <div
                key={entity.id}
                className={`p-4 rounded-xl border transition-all ${
                  entity.is_abnormal
                    ? 'bg-rose-500/5 border-rose-500/30 hover:border-rose-500/50'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {getEntityIcon(entity.entity_type)}
                    <span className="font-semibold text-xs text-white">{entity.entity_name}</span>
                  </div>

                  {/* Abnormality Indicator */}
                  {entity.entity_type === 'LAB_RESULT' && (
                    <span
                      className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                        entity.is_abnormal
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      }`}
                    >
                      {entity.is_abnormal
                        ? (entity.metadata_json?.deterministic_flag || 'ABNORMAL')
                        : 'NORMAL'}
                    </span>
                  )}
                </div>

                {/* Value Display */}
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-lg font-bold text-white">{entity.value}</span>
                  {entity.unit && <span className="text-xs text-slate-400">{entity.unit}</span>}
                </div>

                {/* Reference Range and Rule Explanation */}
                {entity.reference_range && (
                  <div className="mt-2 text-[11px] text-slate-400 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800/80 flex items-center justify-between">
                    <span>Reference: <strong className="text-slate-300">{entity.reference_range}</strong></span>
                    {entity.is_abnormal && (
                      <span className="text-rose-400 font-mono text-[10px]">Out of range</span>
                    )}
                  </div>
                )}

                {/* Confidence & Metadata tags */}
                <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500">
                  <span>Confidence: {(entity.confidence_score * 100).toFixed(0)}%</span>
                  {entity.metadata_json?.panel && (
                    <span className="text-slate-400">Panel: {entity.metadata_json.panel}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
