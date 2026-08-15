import React, { useState } from 'react';
import { TestTube, AlertTriangle, CheckCircle2, Terminal, ShieldCheck, Copy, Check, ArrowRight } from 'lucide-react';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';

export const TestGuideView = ({ issue, onNextStage }) => {
  if (!issue) return null;

  const [copiedTest, setCopiedTest] = useState(false);
  const [copiedLint, setCopiedLint] = useState(false);

  const {
    repo_full_name,
    github_issue_number,
    repository_contribution_guide = {}
  } = issue;

  const testCommand = repository_contribution_guide.test_command || "pytest";
  const testSource = repository_contribution_guide.test_command_source || "pyproject.toml";
  const isTestVerified = testSource !== 'NOT_VERIFIED' && !testCommand.includes('Not verified');

  const lintCommand = repository_contribution_guide.lint_command;
  const lintSource = repository_contribution_guide.lint_command_source || "NOT_VERIFIED";

  const handleCopyTest = () => {
    navigator.clipboard.writeText(testCommand);
    setCopiedTest(true);
    setTimeout(() => setCopiedTest(false), 2000);
  };

  const handleCopyLint = () => {
    if (lintCommand) {
      navigator.clipboard.writeText(lintCommand);
      setCopiedLint(true);
      setTimeout(() => setCopiedLint(false), 2000);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-nova-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono font-bold text-teal-600 uppercase tracking-wider mb-1">
            Stage 08 — Test & Verify
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 tracking-tight">
            Execute Test Suite & Add Regression Tests
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Every high-quality open-source pull request requires all existing tests passing plus a new regression test covering your bug fix.
          </p>
        </div>

        <ProvenanceBadge type="VERIFIED_FACT" source={`Verified from ${testSource}`} />
      </div>

      {/* 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (7 cols): Test Runners & Checklist */}
        <div className="lg:col-span-7 space-y-6">
          {/* Test Runner Box */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <TestTube className="w-4 h-4 text-teal-600" /> Unit Test Runner Command
              </h2>
              <span className="text-[10px] font-mono text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                src: {testSource}
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 text-slate-100 rounded-xl font-mono text-xs border border-slate-800 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-teal-400 font-bold break-all">
                <Terminal className="w-4 h-4 text-teal-400 shrink-0" />
                <span>$ {testCommand}</span>
              </div>
              <button
                onClick={handleCopyTest}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors shrink-0"
                title="Copy command"
              >
                {copiedTest ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>

            <p className="text-xs text-slate-500 font-medium">
              Run this command locally in your repository root to confirm all tests pass before making a pull request.
            </p>
          </div>

          {/* Lint / Format Command if available */}
          {lintCommand && (
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-blue-600" /> Linter / Formatter Command
                </h2>
                <span className="text-[10px] font-mono text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                  src: {lintSource}
                </span>
              </div>

              <div className="p-3.5 bg-slate-950 text-slate-100 rounded-xl font-mono text-xs border border-slate-800 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-blue-400 font-bold break-all">
                  <Terminal className="w-4 h-4 text-blue-400 shrink-0" />
                  <span>$ {lintCommand}</span>
                </div>
                <button
                  onClick={handleCopyLint}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors shrink-0"
                  title="Copy command"
                >
                  {copiedLint ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          )}

          {/* Regression Test Checklist */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600" /> Regression Test Principles
            </h2>
            <div className="space-y-2 text-xs text-slate-700 font-medium">
              <div className="flex items-start gap-2">
                <span className="text-teal-600 font-bold">✓</span>
                <span>Locate existing test files (e.g. <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-800">tests/</code> directory).</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-teal-600 font-bold">✓</span>
                <span>Add a minimal test case asserting the fixed behavior for issue #{github_issue_number}.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-teal-600 font-bold">✓</span>
                <span>Verify that the test fails without your fix and passes with your fix.</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN (5 cols): Actions & Summary */}
        <div className="lg:col-span-5 space-y-6">
          <div className="p-5 bg-teal-50/70 border border-teal-200 rounded-2xl space-y-2">
            <h3 className="text-xs font-bold text-teal-950 uppercase tracking-wider">
              Testing Golden Rule
            </h3>
            <p className="text-xs text-teal-900 leading-relaxed font-medium">
              Maintainers will merge your pull request with confidence when a clear, isolated unit test proves that the bug is resolved and won't regress in the future.
            </p>
          </div>

          {onNextStage && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-nova-sm text-center space-y-3">
              <h4 className="text-sm font-bold text-slate-900">All tests passing locally?</h4>
              <p className="text-xs text-slate-500">
                Proceed to Stage 9 to format your conventional commit and generate a professional PR description.
              </p>
              <button
                onClick={onNextStage}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-teal-700 hover:bg-teal-600 text-white rounded-xl text-xs font-bold transition-all shadow-nova hover:scale-[1.01]"
              >
                <span>Next Stage: Prepare PR</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestGuideView;
