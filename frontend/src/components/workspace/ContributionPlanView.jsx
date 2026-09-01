import React from 'react';
import { CheckCircle2, ArrowRight, FileText, Code2, Terminal, ShieldCheck, Sparkles } from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';

export const ContributionPlanView = ({ issue, onProceedToCheckpoints }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const steps = issue?.explanation?.step_by_step_plan || [];
  const isInsufficient = !steps || steps.length === 0 || (steps.length === 1 && typeof steps[0] === 'string' && steps[0].includes('INSUFFICIENT_EVIDENCE')) || (steps[0]?.description && steps[0].description.includes('INSUFFICIENT_EVIDENCE'));

  if (isInsufficient) {
    return (
      <div className="max-w-4xl mx-auto p-4 sm:p-8 animate-in fade-in duration-200">
        <div className={`p-6 sm:p-8 border rounded-2xl text-center shadow-nova-sm max-w-lg mx-auto my-12 ${
          isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-amber-50/80 border-amber-200 text-slate-900'
        }`}>
          <FileText className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-teal-400' : 'text-amber-600'}`} />
          <h3 className={`text-base font-bold mb-1 ${isDark ? 'text-white' : 'text-amber-900'}`}>GitNova couldn't verify this yet</h3>
          <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-400' : 'text-amber-700'}`}>
            {typeof steps[0] === 'string' && steps[0].includes('INSUFFICIENT_EVIDENCE') ? steps[0] : (steps[0]?.description || 'Repository evidence was insufficient to generate a verified step-by-step fix plan without risk of hallucination.')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-3 sm:p-6 lg:p-8 space-y-4 sm:space-y-6 animate-in fade-in duration-200">
      {/* Plan Header Card */}
      <div className={`rounded-2xl p-4 sm:p-6 shadow-nova-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 border transition-colors ${
        isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-white border-slate-200/90 text-slate-900'
      }`}>
        <div>
          <div className="text-[11px] font-mono font-bold text-[#34D399] uppercase tracking-wider mb-0.5">
            Stage 06 — Plan Fix Roadmap
          </div>
          <h2 className={`text-lg sm:text-2xl font-extrabold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Step-by-Step Contribution Plan
          </h2>
          <p className={`text-xs font-medium mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
            Follow this grounded roadmap to complete your first contribution.
          </p>
        </div>

        <button
          onClick={onProceedToCheckpoints}
          className="w-full sm:w-auto px-4 sm:px-5 py-2.5 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#064E3B] rounded-xl text-xs font-extrabold transition-all shadow-sm flex items-center justify-center gap-2 shrink-0 hover:scale-[1.02]"
        >
          <span>Start Contribution</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Vertical Steps Progression Cards */}
      <div className="space-y-3 sm:space-y-4">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`rounded-2xl p-4 sm:p-6 shadow-nova-sm flex flex-col sm:flex-row gap-3 sm:gap-5 border transition-colors ${
              isDark ? 'bg-[#08131A] border-slate-800' : 'bg-white border-slate-200/90'
            }`}
          >
            {/* Step Number Circle */}
            <div className="flex items-center sm:items-start justify-between sm:justify-start">
              <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-xl sm:rounded-2xl flex items-center justify-center font-extrabold text-xs sm:text-base shrink-0 border ${
                isDark 
                  ? 'bg-[#071F1B] text-[#34D399] border-emerald-500/30' 
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }`}>
                {step.step_number || idx + 1}
              </div>

              {/* Mobile Only File Badge */}
              {step.target_file && (
                <span className={`sm:hidden font-mono text-[10px] px-2 py-0.5 rounded-md border truncate max-w-[200px] ${
                  isDark 
                    ? 'text-[#34D399] bg-[#071F1B] border-emerald-500/30' 
                    : 'text-emerald-700 bg-emerald-50 border-emerald-200'
                }`}>
                  {step.target_file.split('/').pop()}
                </span>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mb-2">
                <h3 className={`text-sm sm:text-base font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {step.title}
                </h3>
                {step.target_file && (
                  <span className={`hidden sm:inline-flex font-mono text-xs px-2.5 py-0.5 rounded-md border truncate max-w-[260px] ${
                    isDark 
                      ? 'text-[#34D399] bg-[#071F1B] border-emerald-500/30' 
                      : 'text-emerald-700 bg-emerald-50 border-emerald-200'
                  }`}>
                    {step.target_file}
                  </span>
                )}
              </div>

              <p className={`text-xs sm:text-sm leading-relaxed mb-3 ${
                isDark ? 'text-slate-300' : 'text-slate-600'
              }`}>
                {step.description}
              </p>

              {step.target_file && (
                <div className={`p-2.5 sm:p-3 rounded-xl border font-mono text-xs flex items-center gap-2 overflow-x-auto ${
                  isDark 
                    ? 'bg-[#030A0E] border-slate-800 text-slate-300' 
                    : 'bg-slate-50 border-slate-200 text-slate-700'
                }`}>
                  <Code2 className="w-4 h-4 text-[#34D399] shrink-0" />
                  <span className="truncate">Target: {step.target_file}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ContributionPlanView;
