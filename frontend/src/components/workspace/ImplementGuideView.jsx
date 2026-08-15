import React, { useState } from 'react';
import { Wrench, GitBranch, AlertCircle, CheckCircle2, Code2, Copy, Check, ArrowRight } from 'lucide-react';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';

export const ImplementGuideView = ({ issue, onNextStage }) => {
  if (!issue) return null;

  const [copied, setCopied] = useState(false);
  const {
    repo_full_name,
    github_issue_number,
    explanation = {}
  } = issue;

  const relevantLocations = explanation.relevant_locations || [];
  const primaryLocation = relevantLocations[0] || {};
  const targetFile = primaryLocation.file_path || 'src/main.py';
  const repoName = repo_full_name ? repo_full_name.split('/')[1] : 'repo';
  const branchCommand = `git checkout -b fix-${repoName}-${github_issue_number}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(branchCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-nova-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono font-bold text-teal-600 uppercase tracking-wider mb-1">
            Stage 07 — Implementation
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 tracking-tight">
            Write Minimal, Targeted Code Changes
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            GitNova guides your changes — you write the code in your local repository fork. Follow scoped change principles.
          </p>
        </div>

        <ProvenanceBadge type="VERIFIED_FACT" source="Target Location Grounding" />
      </div>

      {/* 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (7 cols): Git Branch & File Edits */}
        <div className="lg:col-span-7 space-y-6">
          {/* Feature Branch Setup */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-teal-600" /> 1. Topic Branch Setup
              </h2>
              <span className="text-[11px] font-mono text-slate-400">git CLI</span>
            </div>

            <div className="p-4 bg-slate-950 text-slate-100 rounded-xl font-mono text-xs border border-slate-800 space-y-2 relative">
              <div className="text-slate-400">$ git checkout main</div>
              <div className="text-slate-400">$ git pull upstream main</div>
              <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-800 text-teal-400 font-bold">
                <span>$ {branchCommand}</span>
                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors shrink-0"
                  title="Copy command"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-500">
              Always branch from an up-to-date <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-800">main</code> branch before editing code.
            </p>
          </div>

          {/* Target Code Modifications */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <Code2 className="w-4 h-4 text-teal-600" /> 2. Target File Modification
            </h2>
            <div className="p-3.5 bg-teal-50/70 border border-teal-200 rounded-xl space-y-1 font-mono text-xs">
              <div className="font-bold text-teal-950">Target File: {targetFile}</div>
              {primaryLocation.symbol_name && (
                <div className="text-teal-800">Target Symbol: {primaryLocation.symbol_name}</div>
              )}
            </div>
            <ul className="space-y-2 text-xs text-slate-700 font-medium pt-1">
              <li className="flex items-start gap-2">
                <span className="text-teal-600 font-bold">✓</span>
                <span>Implement minimal logic changes required to resolve the defect.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-teal-600 font-bold">✓</span>
                <span>Follow the repository's code style and indentation rules.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">⚠</span>
                <span>Avoid collateral edits: Do not format unrelated functions or refactor untouched files.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* RIGHT COLUMN (5 cols): Pitfalls & Next Stage */}
        <div className="lg:col-span-5 space-y-6">
          {/* Pitfalls Card */}
          <div className="p-5 bg-amber-50/90 border border-amber-200 rounded-2xl space-y-2.5">
            <h3 className="text-xs font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wider">
              <AlertCircle className="w-4 h-4 text-amber-600" /> Open-Source Coding Pitfalls
            </h3>
            <p className="text-xs text-amber-800 leading-relaxed font-medium">
              Maintainers review every single diff line. Keeping your pull request diff minimal and focused makes review fast and prevents unexpected regression bugs.
            </p>
          </div>

          {/* Action Card */}
          {onNextStage && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-nova-sm text-center space-y-3">
              <h4 className="text-sm font-bold text-slate-900">Done writing code changes?</h4>
              <p className="text-xs text-slate-500">
                Proceed to Stage 8 to run the verified test suite and add regression test coverage.
              </p>
              <button
                onClick={onNextStage}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-teal-700 hover:bg-teal-600 text-white rounded-xl text-xs font-bold transition-all shadow-nova hover:scale-[1.01]"
              >
                <span>Next Stage: Test & Verify</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImplementGuideView;
