import React from 'react';
import { CheckCircle2, ArrowRight, FileText, Code2, Terminal, ShieldCheck } from 'lucide-react';

export const ContributionPlanView = ({ issue, onProceedToCheckpoints }) => {
  const steps = issue?.explanation?.step_by_step_plan || [];
  const isInsufficient = !steps || steps.length === 0 || (steps.length === 1 && typeof steps[0] === 'string' && steps[0].includes('INSUFFICIENT_EVIDENCE')) || (steps[0]?.description && steps[0].description.includes('INSUFFICIENT_EVIDENCE'));

  if (isInsufficient) {
    return (
      <div className="max-w-4xl mx-auto p-8 animate-in fade-in duration-200">
        <div className="p-8 bg-amber-50/80 border border-amber-200 rounded-2xl text-center shadow-nova-sm max-w-lg mx-auto my-12">
          <FileText className="w-10 h-10 text-amber-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-amber-900 mb-1">GitNova couldn't verify this yet</h3>
          <p className="text-xs text-amber-700 leading-relaxed">
            {typeof steps[0] === 'string' && steps[0].includes('INSUFFICIENT_EVIDENCE') ? steps[0] : (steps[0]?.description || 'Repository evidence was insufficient to generate a verified step-by-step fix plan without risk of hallucination.')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8 animate-in fade-in duration-200">
      <div className="bg-white border border-gray-200/90 rounded-2xl p-6 shadow-nova-sm flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-gray-900 mb-1">Step-by-Step Contribution Plan</h2>
          <p className="text-xs text-gray-500">Follow this clear roadmap to complete your first contribution.</p>
        </div>

        <button
          onClick={onProceedToCheckpoints}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-nova flex items-center gap-2"
        >
          <span>Start Contribution</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Vertical Steps Progression */}
      <div className="space-y-4">
        {steps.map((step, idx) => (
          <div key={idx} className="bg-white border border-gray-200/90 rounded-2xl p-6 shadow-nova-sm flex gap-5">
            <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-extrabold text-base shrink-0 border border-emerald-200">
              {step.step_number || idx + 1}
            </div>

            <div className="flex-1">
              <div className="flex items-center justify-between mb-1.5">
                <h3 className="text-base font-bold text-gray-900">{step.title}</h3>
                {step.target_file && (
                  <span className="font-mono text-xs text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-200">
                    {step.target_file}
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-600 leading-relaxed mb-3">
                {step.description}
              </p>

              {step.target_file && (
                <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 font-mono text-xs text-gray-700 flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Target: {step.target_file}</span>
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
