import React from 'react';
import {
  HelpCircle,
  ShieldCheck,
  BookOpen,
  Code,
  Search,
  FileText,
  Wrench,
  TestTube,
  GitPullRequest,
  CheckCircle,
  Check,
  Compass,
  X
} from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';

export const JourneySidebar = ({ activeStep = 'understand', onSelectStep, completedSteps = [], isOpen = false, onClose, className = '' }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const groups = [
    {
      groupLabel: 'ORIENTATION',
      items: [
        { id: 'understand', num: '01', label: 'Understand', icon: HelpCircle },
        { id: 'check_status', num: '02', label: 'Check Status', icon: ShieldCheck }
      ]
    },
    {
      groupLabel: 'KNOWLEDGE & CODE',
      items: [
        { id: 'learn', num: '03', label: 'Learn Concepts', icon: BookOpen },
        { id: 'explore', num: '04', label: 'Explore Code', icon: Code },
        { id: 'investigate', num: '05', label: 'Investigate', icon: Search }
      ]
    },
    {
      groupLabel: 'EXECUTION',
      items: [
        { id: 'plan', num: '06', label: 'Plan Fix', icon: FileText },
        { id: 'implement', num: '07', label: 'Implement', icon: Wrench },
        { id: 'test', num: '08', label: 'Test', icon: TestTube }
      ]
    },
    {
      groupLabel: 'CONTRIBUTION',
      items: [
        { id: 'prepare_pr', num: '09', label: 'Prepare PR', icon: GitPullRequest },
        { id: 'review', num: '10', label: 'Review', icon: CheckCircle }
      ]
    }
  ];

  const totalSteps = 10;
  const completedCount = completedSteps.length;
  const progressPercent = Math.min(100, Math.round((completedCount / totalSteps) * 100));

  const handleStepClick = (stepId) => {
    onSelectStep(stepId);
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-200"
          aria-hidden="true"
        />
      )}

      {/* Main Journey Sidebar (Desktop Sticky + Mobile Drawer) */}
      <aside
        className={`w-64 flex flex-col shrink-0 h-screen overflow-y-auto custom-scrollbar transition-transform duration-300 ease-in-out z-50
          bg-white dark:bg-[#08131A]
          border-r border-slate-200/90 dark:border-slate-800
          fixed md:sticky top-0 inset-y-0 left-0
          ${isOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'}
          ${className}`}
      >
        {/* Header with Mission Progress & Mobile Close */}
        <div className={`p-4 border-b transition-colors ${
          isDark ? 'border-slate-800 bg-[#0B1B24]' : 'border-slate-100 bg-slate-50/50'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 min-w-0">
              <Compass className="w-3.5 h-3.5 text-[#34D399] shrink-0" />
              <span className={`text-[11px] font-bold uppercase tracking-wider truncate ${
                isDark ? 'text-white' : 'text-slate-800'
              }`}>
                Contribution Journey
              </span>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                isDark 
                  ? 'text-[#34D399] bg-[#071F1B] border-emerald-500/30' 
                  : 'text-teal-700 bg-teal-50 border-teal-200'
              }`}>
                {completedCount}/{totalSteps}
              </span>

              {onClose && (
                <button
                  onClick={onClose}
                  className="p-1 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white md:hidden"
                  aria-label="Close stages menu"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className={`w-full h-1.5 rounded-full overflow-hidden ${
            isDark ? 'bg-slate-800' : 'bg-slate-200'
          }`}>
            <div
              className="bg-gradient-to-r from-teal-500 to-emerald-400 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.max(5, progressPercent)}%` }}
            />
          </div>
        </div>

        {/* Navigation Group Items */}
        <div className="p-3 space-y-4 flex-1">
          {groups.map((group) => (
            <div key={group.groupLabel}>
              <div className="text-[10px] font-extrabold text-slate-400 tracking-wider uppercase mb-1.5 px-2">
                {group.groupLabel}
              </div>
              <div className="space-y-0.5">
                {group.items.map((step) => {
                  const Icon = step.icon;
                  const isActive = activeStep === step.id;
                  const isCompleted = completedSteps.includes(step.id);

                  return (
                    <button
                      key={step.id}
                      onClick={() => handleStepClick(step.id)}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-all text-left ${
                        isActive
                          ? (isDark 
                              ? 'text-[#34D399] bg-[#071F1B] font-bold border border-emerald-500/30 shadow-sm' 
                              : 'text-teal-900 bg-teal-50/90 font-bold border border-teal-200 shadow-nova-sm')
                          : isCompleted
                          ? (isDark ? 'text-slate-200 hover:bg-slate-800/60' : 'text-slate-700 hover:bg-slate-50')
                          : (isDark ? 'text-slate-400 hover:text-white hover:bg-slate-800/60' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50')
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div
                          className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs shrink-0 transition-all ${
                            isActive
                              ? 'bg-[#34D399] text-[#052E2B] shadow-nova-sm'
                              : isCompleted
                              ? (isDark ? 'bg-[#07241F] text-[#34D399]' : 'bg-teal-100 text-teal-700')
                              : (isDark ? 'bg-[#0D1F2B] text-slate-400' : 'bg-slate-100 text-slate-400')
                          }`}
                        >
                          {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : <Icon className="w-3.5 h-3.5" />}
                        </div>
                        <span className="truncate">{step.label}</span>
                      </div>

                      <span className="text-[10px] font-mono text-slate-400 shrink-0 ml-1">
                        {step.num}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
};

export default JourneySidebar;
