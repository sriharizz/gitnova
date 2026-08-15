import React from 'react';
import { Check } from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';

export const StepperProgress = ({ steps = [], currentStep = 1, onStepClick }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`inline-flex items-center justify-center gap-3 sm:gap-4 px-6 py-2.5 rounded-full border transition-all ${
      isDark 
        ? 'bg-[#081722]/90 border-slate-700/80 shadow-[0_4px_20px_rgba(0,0,0,0.5)] backdrop-blur-md' 
        : 'bg-white/90 border-slate-200 shadow-sm backdrop-blur-md'
    }`}>
      {steps.map((step, idx) => {
        const stepNum = idx + 1;
        const isCompleted = stepNum < currentStep;
        const isActive = stepNum === currentStep;

        return (
          <React.Fragment key={step.id || idx}>
            <div 
              onClick={() => isCompleted && onStepClick && onStepClick(stepNum)}
              className={`flex items-center gap-2 transition-all select-none ${
                isCompleted 
                  ? (isDark ? 'text-[#34D399] cursor-pointer hover:opacity-80' : 'text-teal-700 cursor-pointer hover:opacity-80') 
                  : isActive 
                  ? (isDark ? 'text-white font-bold' : 'text-slate-900 font-bold') 
                  : (isDark ? 'text-slate-400' : 'text-slate-400')
              }`}
            >
              <div 
                className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-xs font-extrabold transition-all duration-200 ${
                  isCompleted 
                    ? 'bg-[#34D399] text-[#052E2B] shadow-[0_0_12px_rgba(52,211,153,0.4)]' 
                    : isActive 
                    ? (isDark 
                        ? 'bg-[#34D399] text-[#052E2B] shadow-[0_0_18px_rgba(52,211,153,0.6)] ring-2 ring-[#34D399]/40' 
                        : 'bg-teal-700 text-white shadow-[0_0_12px_rgba(15,118,110,0.3)] ring-2 ring-teal-600/30')
                    : (isDark ? 'bg-[#0D212E] text-slate-400 border border-slate-700' : 'bg-slate-100 text-slate-400 border border-slate-200')
                }`}
              >
                {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[3]" /> : stepNum}
              </div>
              <span className="text-xs sm:text-sm font-semibold tracking-tight">{step.label}</span>
            </div>

            {idx < steps.length - 1 && (
              <div 
                className={`h-0.5 w-6 sm:w-10 rounded-full transition-all duration-300 ${
                  stepNum < currentStep 
                    ? 'bg-gradient-to-r from-[#34D399] to-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' 
                    : (isDark ? 'bg-slate-700' : 'bg-slate-200')
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default StepperProgress;
