import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Activity, 
  UserCheck, 
  MessageSquareHeart, 
  FileText, 
  ClipboardCheck, 
  ShieldCheck,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { fetchHealth } from '../../api/client';

const STEPS = [
  { path: '/identify', label: '1. Identification', icon: UserCheck },
  { path: '/converse', label: '2. Conversation', icon: MessageSquareHeart },
  { path: '/documents', label: '3. Documents', icon: FileText },
  { path: '/summary', label: '4. Summary Review', icon: ClipboardCheck },
  { path: '/consent', label: '5. Consent & Export', icon: ShieldCheck },
];


export const Layout: React.FC = () => {
  const location = useLocation();
  const { data: health, isError } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchHealth,
    refetchInterval: 10000,
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Header Bar */}
      <header className="glass-panel sticky top-0 z-50 px-6 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Health AI <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">Pre-Consultation Platform</span>
            </h1>
            <p className="text-xs text-slate-400">Clinical History & Structured ABDM/FHIR Integration</p>
          </div>
        </div>

        {/* System Health Status Badge */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-lg glass-card">
            <span className="text-slate-400">System API:</span>
            {isError ? (
              <span className="flex items-center gap-1 text-rose-400 font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> Disconnected
              </span>
            ) : health?.status === 'healthy' ? (
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> Operational ({health.environment})
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-400 font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> Degraded
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Workflow Navigation Step Bar */}
      <div className="border-b border-slate-800/80 bg-slate-900/60 px-6 py-2">
        <div className="max-w-7xl mx-auto flex items-center justify-between overflow-x-auto gap-2 py-1">
          {STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = location.pathname.startsWith(step.path);
            return (
              <NavLink
                key={step.path}
                to={step.path}
                className={({ isActive }) =>
                  `flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                    isActive
                      ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`
                }
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-slate-400'}`} />
                <span>{step.label}</span>
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-4 px-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span>Healthcare AI Pre-Consultation Prototype • Deterministic Safety Layer & Structured Output</span>
          <span>FastAPI + SQLAlchemy 2 + React + TypeScript</span>
        </div>
      </footer>
    </div>
  );
};
