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
  Compass
} from 'lucide-react';

export const JourneySidebar = ({ activeStep = 'understand', onSelectStep, completedSteps = [] }) => {
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

  return (
    <aside className="w-64 bg-white border-r border-slate-200/90 flex flex-col shrink-0 h-screen sticky top-0 z-20 overflow-y-auto custom-scrollbar">
      {/* Header with Mission Progress */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-teal-600" />
            <span className="text-[11px] font-bold text-slate-800 uppercase tracking-wider">
              Contribution Journey
            </span>
          </div>
          <span className="text-[10px] font-mono font-bold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
            {completedCount}/{totalSteps}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-gradient-to-r from-teal-500 to-emerald-500 h-full rounded-full transition-all duration-300"
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
                    onClick={() => onSelectStep(step.id)}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-all text-left ${
                      isActive
                        ? 'text-teal-900 bg-teal-50/90 font-bold border border-teal-200 shadow-nova-sm'
                        : isCompleted
                        ? 'text-slate-700 hover:bg-slate-50'
                        : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs shrink-0 transition-all ${
                          isActive
                            ? 'bg-teal-600 text-white shadow-nova-sm'
                            : isCompleted
                            ? 'bg-teal-100 text-teal-700'
                            : 'bg-slate-100 text-slate-400'
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
  );
};

export default JourneySidebar;
