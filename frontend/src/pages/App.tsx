import React, { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  UserCheck,
  MessageSquareHeart,
  FileText,
  ClipboardCheck,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Menu,
  X,
  ChevronRight,
  RefreshCw,
  Sparkles,
  Server,
  Layers,
  HeartHandshake,
  ExternalLink,
} from 'lucide-react';
import { fetchHealth } from '../api/client';
import { ToastProvider, useToast } from '../components/common/Toast';
import { ErrorBoundary } from '../components/common/ErrorBoundary';

interface NavItem {
  path: string;
  label: string;
  description: string;
  icon: React.ElementType;
  badge?: string;
  stepNumber: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: '/identify',
    label: 'Patient Intake',
    description: 'ABHA lookup & system mode',
    icon: UserCheck,
    stepNumber: '01',
  },
  {
    path: '/converse',
    label: 'Conversations',
    description: 'SOCRATES clinical interview',
    icon: MessageSquareHeart,
    badge: 'Prompt 9',
    stepNumber: '02',
  },
  {
    path: '/documents',
    label: 'Documents',
    description: 'Digitization & lab extraction',
    icon: FileText,
    badge: 'Prompt 10',
    stepNumber: '03',
  },
  {
    path: '/summary',
    label: 'Summaries',
    description: 'Structured review & sign-off',
    icon: ClipboardCheck,
    badge: 'Prompt 11',
    stepNumber: '04',
  },
  {
    path: '/consent',
    label: 'Consent & FHIR',
    description: 'Auditable ABDM export sandbox',
    icon: ShieldCheck,
    stepNumber: '05',
  },
];

const MainLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const location = useLocation();
  const navigate = useNavigate();
  const toast = useToast();

  const activeSessionId = localStorage.getItem('active_session_id');

  // Poll system health
  const { data: health, isError, refetch: refetchHealth, isFetching: isCheckingHealth } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchHealth,
    refetchInterval: 15000,
    retry: 1,
  });

  const handleResetSession = () => {
    localStorage.removeItem('active_session_id');
    toast.info('Active consultation session cleared. Starting fresh.', 'Session Reset');
    navigate('/identify');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-brand-500 selection:text-white">
      {/* Top Header Bar */}
      <header className="sticky top-0 z-40 h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-4 lg:px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 lg:hidden transition-colors"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          {/* Desktop sidebar toggle button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden lg:flex p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Logo Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 via-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">Health AI</span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  Pre-Consultation Platform
                </span>
              </div>
              <p className="hidden sm:block text-[11px] text-slate-400">
                Clinical History Taking • Document Digitization • Structured ABDM/FHIR
              </p>
            </div>
          </div>
        </div>

        {/* Right Header Status / Controls */}
        <div className="flex items-center gap-3">
          {/* Active Session Indicator */}
          {activeSessionId && (
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
              <span className="text-slate-400">Session:</span>
              <span className="font-mono text-brand-300 font-semibold truncate max-w-[120px]">
                {activeSessionId.slice(0, 12)}...
              </span>
              <button
                onClick={handleResetSession}
                className="text-slate-500 hover:text-rose-400 transition-colors ml-1 p-0.5"
                title="Clear current session and reset"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* System API Health Badge */}
          <div
            onClick={() => refetchHealth()}
            className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-xl border border-slate-800/80 bg-slate-900/50 hover:bg-slate-900 transition-all cursor-pointer select-none"
            title="Click to recheck API connection status"
          >
            <span className="text-slate-400 hidden sm:inline">Backend API:</span>
            {isCheckingHealth ? (
              <span className="flex items-center gap-1.5 text-brand-400 font-medium">
                <RefreshCw className="w-3 h-3 animate-spin" /> Checking...
              </span>
            ) : isError ? (
              <span className="flex items-center gap-1.5 text-rose-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                <AlertCircle className="w-3.5 h-3.5" /> Offline
              </span>
            ) : health?.status === 'healthy' ? (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected ({health.environment || 'local'})
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-amber-400 font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> Degraded
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Layout with Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar for Desktop */}
        <aside
          className={`hidden lg:flex flex-col border-r border-slate-800/80 bg-slate-950/60 backdrop-blur-md transition-all duration-300 ease-in-out shrink-0 z-30 ${
            sidebarOpen ? 'w-64' : 'w-20'
          }`}
        >
          {/* Navigation Items */}
          <div className="p-3 space-y-1.5 flex-1 overflow-y-auto">
            <div className={`px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400 ${!sidebarOpen && 'text-center'}`}>
              {sidebarOpen ? 'Workflow Navigation' : 'Nav'}
            </div>

            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const targetUrl =
                item.path !== '/identify' && activeSessionId
                  ? `${item.path}?session_id=${activeSessionId}`
                  : item.path;
              const isCurrent = location.pathname.startsWith(item.path);

              return (
                <NavLink
                  key={item.path}
                  to={targetUrl}
                  className={`group flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${
                    isCurrent
                      ? 'bg-brand-500/15 text-brand-300 border border-brand-500/30 shadow-sm shadow-brand-500/5'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                  } ${!sidebarOpen ? 'justify-center px-2' : ''}`}
                  title={!sidebarOpen ? `${item.label} — ${item.description}` : undefined}
                >
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                      isCurrent
                        ? 'bg-brand-500 text-slate-950 font-bold'
                        : 'bg-slate-900 text-slate-400 group-hover:text-white group-hover:bg-slate-800'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>

                  {sidebarOpen && (
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="truncate font-medium">{item.label}</span>
                        {item.badge && (
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 group-hover:text-slate-300">
                            {item.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {item.description}
                      </p>
                    </div>
                  )}
                </NavLink>
              );
            })}
          </div>

          {/* Sidebar Footer Info */}
          {sidebarOpen ? (
            <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 text-xs text-slate-400 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium">Architecture</span>
                <span className="text-brand-400 font-mono">Monolith v1</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/60 text-[11px] space-y-1">
                <div className="flex items-center gap-1.5 text-slate-300">
                  <HeartHandshake className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                  <span>Deterministic Guard</span>
                </div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  LLM is not source of truth. Rules control clinical escalations.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-3 border-t border-slate-800/80 flex justify-center">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-500 animate-pulse" title="System active" />
            </div>
          )}
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 lg:hidden flex">
            <div
              className="fixed inset-0 bg-black/80 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative w-72 max-w-[80vw] bg-slate-950 border-r border-slate-800 p-4 flex flex-col h-full z-10 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-brand-400" />
                  <span className="font-bold text-white">Health AI Menu</span>
                </div>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-1.5 flex-1 overflow-y-auto">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  const targetUrl =
                    item.path !== '/identify' && activeSessionId
                      ? `${item.path}?session_id=${activeSessionId}`
                      : item.path;
                  const isCurrent = location.pathname.startsWith(item.path);

                  return (
                    <NavLink
                      key={item.path}
                      to={targetUrl}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 p-3 rounded-xl text-sm font-medium transition-all ${
                        isCurrent
                          ? 'bg-brand-500/15 text-brand-300 border border-brand-500/30'
                          : 'text-slate-400 hover:text-white hover:bg-slate-900'
                      }`}
                    >
                      <Icon className="w-5 h-5 shrink-0 text-brand-400" />
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold">{item.label}</div>
                        <div className="text-[11px] text-slate-400">{item.description}</div>
                      </div>
                    </NavLink>
                  );
                })}
              </div>

              {activeSessionId && (
                <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                  <div className="text-slate-400 mb-1">Active Session</div>
                  <div className="font-mono text-brand-300 text-xs truncate">{activeSessionId}</div>
                  <button
                    onClick={() => {
                      handleResetSession();
                      setMobileMenuOpen(false);
                    }}
                    className="mt-2 w-full py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-medium border border-rose-500/20 transition-colors"
                  >
                    Reset Session
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Content Area Wrapped with Error Boundary */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-gradient-to-b from-slate-950 via-slate-900/30 to-slate-950">
          <div className="max-w-7xl mx-auto w-full">
            <ErrorBoundary
              fallbackTitle="Clinical Module Error"
              fallbackMessage="There was a problem rendering this clinical module view. You can refresh or switch to another section."
            >
              <Outlet />
            </ErrorBoundary>
          </div>
        </main>
      </div>

      {/* Global Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950/80 py-3 px-6 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Healthcare AI Pre-Consultation Monolith • Auditable ABDM / FHIR Integration</span>
          </div>
          <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
            <span>FastAPI Backend</span>
            <span>•</span>
            <span>React + TypeScript</span>
            <span>•</span>
            <span>SQLAlchemy 2</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const AppLayout: React.FC = () => {
  return (
    <ToastProvider>
      <MainLayout />
    </ToastProvider>
  );
};

export default AppLayout;
