import React, { useState } from 'react';
import { CheckCircle2, ExternalLink, ShieldCheck, AlertCircle, RefreshCw, PartyPopper, Check } from 'lucide-react';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';

export const ReviewChecklistView = ({ issue }) => {
  if (!issue) return null;

  const {
    repo_full_name,
    github_issue_number,
    title,
    github_url
  } = issue;

  const [checkedItems, setCheckedItems] = useState({});

  const toggleCheck = (id) => {
    setCheckedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const checklist = [
    { id: 'c1', text: `Does your code change directly resolve issue #${github_issue_number}?` },
    { id: 'c2', text: "Did you add or update regression unit tests covering your fix?" },
    { id: 'c3', text: "Do all unit tests pass locally without errors?" },
    { id: 'c4', text: "Did you follow repository contribution and code style guidelines?" },
    { id: 'c5', text: "Are unrelated code files and whitespace/formatting untouched?" },
    { id: 'c6', text: "Is the issue still open on GitHub with no conflicting PR merged?" },
    { id: 'c7', text: "Does your PR description explicitly contain 'Fixes #X'?" }
  ];

  const completedCount = Object.values(checkedItems).filter(Boolean).length;
  const isReady = completedCount === checklist.length;
  const percentComplete = Math.round((completedCount / checklist.length) * 100);

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-nova-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono font-bold text-teal-600 uppercase tracking-wider mb-1">
            Stage 10 — Pre-Submission Review
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 tracking-tight">
            Final Contribution Readiness Checklist
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Perform a rigorous final quality check before opening your Pull Request on GitHub.
          </p>
        </div>

        <ProvenanceBadge type="VERIFIED_FACT" source="Pre-Flight Validation Standard" />
      </div>

      {/* 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (7 cols): Checklist */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-nova-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600" /> Pre-Submission Items ({completedCount}/{checklist.length})
              </h2>
              <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                isReady
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}>
                {isReady ? '✓ Ready to Submit' : `${percentComplete}% Complete`}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-600 transition-all duration-300 rounded-full"
                style={{ width: `${percentComplete}%` }}
              />
            </div>

            <div className="space-y-2 pt-1">
              {checklist.map((item) => {
                const checked = !!checkedItems[item.id];
                return (
                  <button
                    key={item.id}
                    onClick={() => toggleCheck(item.id)}
                    className={`w-full flex items-start gap-3 p-3.5 rounded-xl border text-left transition-all ${
                      checked
                        ? 'bg-teal-50/60 border-teal-200 text-teal-950 font-semibold shadow-nova-sm'
                        : 'bg-slate-50 border-slate-200/80 text-slate-700 hover:bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 mt-0.5 transition-all ${
                      checked ? 'bg-teal-600 border-teal-600 text-white' : 'bg-white border-slate-300'
                    }`}>
                      {checked && <Check className="w-3 h-3 stroke-[3]" />}
                    </div>
                    <span className="text-xs leading-relaxed">{item.text}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN (5 cols): GitHub Link & Completion Card */}
        <div className="lg:col-span-5 space-y-6">
          {/* Re-Check GitHub Callout */}
          <div className="p-5 bg-slate-900 text-slate-100 rounded-2xl border border-slate-800 shadow-nova-md space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-white">
                <ShieldCheck className="w-4 h-4 text-teal-400" /> Re-Check GitHub Status
              </h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Verify one final time that the issue is still open and no one else opened a competing PR while you worked.
            </p>

            <a
              href={github_url || `https://github.com/${repo_full_name}/issues/${github_issue_number}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold transition-all shadow-nova"
            >
              <span>Open GitHub Issue #{github_issue_number}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Congratulations Card */}
          {isReady && (
            <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl shadow-nova text-center space-y-2 animate-in zoom-in-95 duration-200">
              <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-2">
                <PartyPopper className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-extrabold text-emerald-950">You're Ready to Submit!</h3>
              <p className="text-xs text-emerald-800 leading-relaxed">
                All 7 quality criteria are verified. Open your PR with confidence and tag GitNova in your contribution journey!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReviewChecklistView;
