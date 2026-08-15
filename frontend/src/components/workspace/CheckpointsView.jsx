import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, ExternalLink, Sparkles, Trophy, GitPullRequest } from 'lucide-react';

export const CheckpointsView = ({ issue }) => {
  const issueId = issue?.id || 'default';
  
  const [checkedState, setCheckedState] = useState(() => {
    const saved = localStorage.getItem(`gitnova_checkpoints_${issueId}`);
    return saved ? JSON.parse(saved) : [true, true, false, false, false, false];
  });

  const checkpointItems = [
    { label: "Understand the issue", hint: "Read the plain-English summary and root cause explanation." },
    { label: "Locate the relevant code", hint: "Review the verified file locations in Code Explorer." },
    { label: "Understand the implementation", hint: "Inspect symbol definitions and methods in focus." },
    { label: "Make the change", hint: "Fork repo, create branch, and apply modifications." },
    { label: "Run tests", hint: "Run existing test suite to ensure zero regressions." },
    { label: "Prepare PR", hint: "Commit changes, push to GitHub, and open Pull Request." }
  ];

  const toggleCheck = (idx) => {
    const updated = [...checkedState];
    updated[idx] = !updated[idx];
    setCheckedState(updated);
    localStorage.setItem(`gitnova_checkpoints_${issueId}`, JSON.stringify(updated));
  };

  const completedCount = checkedState.filter(Boolean).length;
  const progressPct = Math.round((completedCount / checkpointItems.length) * 100);

  const githubUrl = issue?.github_url || `https://github.com/${issue?.repo_full_name || 'pallets/flask'}/issues`;

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8 animate-in fade-in duration-200">
      {/* Progress Header Card */}
      <div className="bg-white border border-gray-200/90 rounded-2xl p-6 shadow-nova-sm flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Trophy className="w-5 h-5 text-amber-500" />
            <h2 className="text-xl font-bold text-gray-900">Contribution Progress</h2>
          </div>
          <p className="text-xs text-gray-500">Track your progress from understanding to final GitHub PR.</p>
        </div>

        <div className="text-right">
          <div className="text-2xl font-extrabold text-emerald-600">{progressPct}%</div>
          <div className="text-xs text-gray-400 font-medium">{completedCount} of 6 completed</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden">
        <div 
          className="bg-emerald-500 h-full transition-all duration-500 rounded-full"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Checkpoints List */}
      <div className="bg-white border border-gray-200/90 rounded-2xl p-6 shadow-nova-sm space-y-4">
        {checkpointItems.map((item, idx) => {
          const isChecked = checkedState[idx];

          return (
            <div 
              key={idx}
              onClick={() => toggleCheck(idx)}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-4 ${
                isChecked
                  ? 'bg-emerald-50/50 border-emerald-200 text-gray-900'
                  : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isChecked ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-100" />
                ) : (
                  <Circle className="w-5 h-5 text-gray-300" />
                )}
              </div>

              <div>
                <div className={`text-sm font-bold ${isChecked ? 'text-emerald-900 line-through opacity-80' : 'text-gray-900'}`}>
                  {item.label}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {item.hint}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Final GitHub Handoff Hero Box */}
      <div className="bg-gradient-to-br from-emerald-900 via-emerald-800 to-gray-900 text-white rounded-3xl p-8 shadow-nova-lg relative overflow-hidden">
        <div className="relative z-10 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/20 border border-emerald-400/30 rounded-full text-emerald-300 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ready for GitHub</span>
          </div>

          <h2 className="text-2xl md:text-3xl font-extrabold mb-3">
            You're ready to contribute!
          </h2>

          <p className="text-emerald-100/90 text-sm leading-relaxed mb-6">
            GitNova has guided you through understanding the issue, locating the code, and building your plan. Now head to GitHub to claim the issue or submit your Pull Request.
          </p>

          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 px-7 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-white font-extrabold text-sm rounded-xl transition-all shadow-nova hover:scale-[1.02]"
          >
            <GitPullRequest className="w-4 h-4" />
            <span>View issue on GitHub</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};

export default CheckpointsView;
