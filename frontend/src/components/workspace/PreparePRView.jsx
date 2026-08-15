import React, { useState } from 'react';
import { GitPullRequest, GitCommit, ExternalLink, ShieldCheck, AlertCircle, Copy, Check, ArrowRight } from 'lucide-react';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';

export const PreparePRView = ({ issue, onNextStage }) => {
  if (!issue) return null;

  const [copiedCommit, setCopiedCommit] = useState(false);
  const [copiedTemplate, setCopiedTemplate] = useState(false);

  const {
    repo_full_name,
    github_issue_number,
    repository_contribution_guide = {},
    github_url
  } = issue;

  const primaryLocation = issue.explanation?.relevant_locations?.[0] || {};
  const targetSymbol = primaryLocation.symbol_name || 'fix';
  const prGuidance = repository_contribution_guide.pull_request_guidance;
  const claRequired = repository_contribution_guide.cla_required;
  const commitMsg = `fix: resolve issue #${github_issue_number} in ${targetSymbol}`;

  const prTemplateText = `## Description\nFixes #${github_issue_number}\n\nResolved issue in ${primaryLocation.file_path || 'target file'} by ensuring proper parameter handling.\n\n## Testing\n- Executed existing test suite\n- Added regression unit test covering issue #${github_issue_number}`;

  const handleCopyCommit = () => {
    navigator.clipboard.writeText(commitMsg);
    setCopiedCommit(true);
    setTimeout(() => setCopiedCommit(false), 2000);
  };

  const handleCopyTemplate = () => {
    navigator.clipboard.writeText(prTemplateText);
    setCopiedTemplate(true);
    setTimeout(() => setCopiedTemplate(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-nova-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono font-bold text-teal-600 uppercase tracking-wider mb-1">
            Stage 09 — Prepare Pull Request
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 tracking-tight">
            Format Commit & Open Pull Request
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Format conventional commit messages and prepare clear maintainer-friendly PR descriptions.
          </p>
        </div>

        <a
          href={`https://github.com/${repo_full_name}/compare`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition-all shadow-nova-sm"
        >
          <span>Open PR on GitHub</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (7 cols): Commit & Description */}
        <div className="lg:col-span-7 space-y-6">
          {/* Commit Formatting */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <GitCommit className="w-4 h-4 text-teal-600" /> 1. Conventional Commit Message
              </h2>
              <span className="text-[10px] font-mono text-slate-400">git commit</span>
            </div>

            <div className="p-3.5 bg-slate-950 text-slate-100 rounded-xl font-mono text-xs border border-slate-800 flex items-center justify-between gap-2">
              <span className="text-teal-400 font-bold break-all">$ git commit -m "{commitMsg}"</span>
              <button
                onClick={handleCopyCommit}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors shrink-0"
                title="Copy commit command"
              >
                {copiedCommit ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Use imperative mood (e.g. "fix: resolve..." rather than "fixed...").
            </p>
          </div>

          {/* PR Description Template */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <GitPullRequest className="w-4 h-4 text-teal-600" /> 2. PR Body Description Template
              </h2>
              <button
                onClick={handleCopyTemplate}
                className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-600 hover:text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 transition-colors"
              >
                {copiedTemplate ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                <span>{copiedTemplate ? 'Copied' : 'Copy Template'}</span>
              </button>
            </div>

            {prGuidance && (
              <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-xs text-teal-950 font-semibold">
                Maintainer Guidance: {prGuidance}
              </div>
            )}

            <pre className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed">
              {prTemplateText}
            </pre>
          </div>
        </div>

        {/* RIGHT COLUMN (5 cols): CLA & Next Stage */}
        <div className="lg:col-span-5 space-y-6">
          {claRequired ? (
            <div className="p-5 bg-amber-50/90 border border-amber-200 rounded-2xl space-y-2">
              <h3 className="text-xs font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wider">
                <AlertCircle className="w-4 h-4 text-amber-600" /> CLA / DCO Agreement Required
              </h3>
              <p className="text-xs text-amber-800 leading-relaxed font-medium">
                This repository requires signing a Contributor License Agreement (CLA) or Developer Certificate of Origin (DCO). Look for the automated bot comment on your PR once opened.
              </p>
            </div>
          ) : (
            <div className="p-5 bg-teal-50/70 border border-teal-200 rounded-2xl space-y-2">
              <h3 className="text-xs font-bold text-teal-950 uppercase tracking-wider">
                Standard Contribution Policy
              </h3>
              <p className="text-xs text-teal-900 leading-relaxed font-medium">
                Standard open-source pull request workflow applies. Link the issue using <code className="bg-white/80 px-1 py-0.5 rounded font-mono text-teal-800 font-bold">Fixes #{github_issue_number}</code> so GitHub auto-closes it upon merge.
              </p>
            </div>
          )}

          {onNextStage && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-nova-sm text-center space-y-3">
              <h4 className="text-sm font-bold text-slate-900">PR ready to submit?</h4>
              <p className="text-xs text-slate-500">
                Proceed to Stage 10 for the final pre-submission verification checklist.
              </p>
              <button
                onClick={onNextStage}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-teal-700 hover:bg-teal-600 text-white rounded-xl text-xs font-bold transition-all shadow-nova hover:scale-[1.01]"
              >
                <span>Next Stage: Final Review Checklist</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PreparePRView;
