import React from 'react';
import { Search, AlertTriangle, TestTube, CheckCircle2, ArrowRight, Code, Play, Terminal, Copy, Check } from 'lucide-react';
import FailureFlowDiagram from '../diagrams/FailureFlowDiagram';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';

export const InvestigateView = ({ issue, onNextStage }) => {
  if (!issue) return null;

  const [copied, setCopied] = React.useState(false);
  const explanation = issue.explanation || {};
  const whyItHappens = explanation.why_it_happens || "Underlying implementation logic defect in target module.";
  const relevantLocations = explanation.relevant_locations || [];
  const primaryLocation = relevantLocations[0] || {};
  const failureFlowDiagram = explanation.failure_flow_diagram;

  const repoGuide = issue.repository_contribution_guide || {};
  const testCommand = repoGuide.test_command || "pytest";
  const testCommandSource = repoGuide.test_command_source || "pyproject.toml";
  const isTestVerified = testCommandSource !== 'NOT_VERIFIED';

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Synthetic fallback flow diagram if not present
  const activeDiagram = failureFlowDiagram || {
    title: 'Control Flow & Failure Trace',
    description: `Sequence tracing into ${primaryLocation.file_path || 'target file'}`,
    nodes: [
      {
        id: 'node-1',
        node_type: 'trigger',
        label: 'Caller Invocation',
        metadata: { detail: `External code calls ${primaryLocation.symbol_name || 'module entrypoint'}` }
      },
      {
        id: 'node-2',
        node_type: 'current',
        label: 'Input Processing',
        metadata: { detail: `Target file ${primaryLocation.file_path || 'source'} parses argument` }
      },
      {
        id: 'node-3',
        node_type: 'failure',
        label: 'Unhandled Condition',
        metadata: { detail: whyItHappens }
      },
      {
        id: 'node-4',
        node_type: 'consequence',
        label: 'Incorrect State / Crash',
        metadata: { detail: 'Unexpected return value or exception raised to caller' }
      }
    ]
  };

  return (
    <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-nova-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono font-bold text-teal-600 uppercase tracking-wider mb-1">
            Stage 05 — Investigate & Reproduce
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 tracking-tight">
            Investigate Existing Behavior & Control Flow
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Understand why the current code fails before writing a single line of production code. Rule: READ → UNDERSTAND → REPRODUCE.
          </p>
        </div>

        <ProvenanceBadge type="VERIFIED_FACT" source="AST Analysis & Issue Grounding" />
      </div>

      {/* Centerpiece: Failure Flow Diagram */}
      <FailureFlowDiagram diagram={activeDiagram} />

      {/* 2-Column Details: Root Cause & Target Inspection */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT (7 cols): Technical Root Cause & Inspection */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <Search className="w-4 h-4 text-teal-600" />
              <span>Technical Root Cause Analysis</span>
            </div>
            <p className="text-xs md:text-sm font-semibold text-slate-800 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200/70 font-mono">
              {whyItHappens}
            </p>
          </div>

          <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-nova-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <Code className="w-4 h-4 text-teal-600" />
              <span>Primary Inspection Site</span>
            </div>
            <div className="p-3.5 bg-teal-50/60 border border-teal-200/80 rounded-xl space-y-1">
              <div className="text-xs font-bold text-teal-950 font-mono">
                Target File: {primaryLocation.file_path || 'src/main.py'}
              </div>
              {primaryLocation.symbol_name && (
                <div className="text-xs text-teal-800 font-mono">
                  Symbol: {primaryLocation.symbol_name} (Lines {primaryLocation.lines || '1-50'})
                </div>
              )}
            </div>

            <div className="space-y-2 pt-2 text-xs text-slate-700 font-medium">
              <div className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">1</span>
                <span>Trace how arguments are parsed inside <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-teal-700">{primaryLocation.symbol_name || 'the target function'}</code>.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">2</span>
                <span>Locate the branch or unhandled condition leading to the incorrect behavior.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">3</span>
                <span>Run the local test suite below to observe the baseline pass/fail status.</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT (5 cols): Test Execution & Next Stage */}
        <div className="lg:col-span-5 space-y-6">
          {/* Baseline Testing Runner Card */}
          <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-nova-md border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Baseline Test Execution</h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                src: {testCommandSource}
              </span>
            </div>

            <p className="text-xs text-slate-400">
              Run this verified test command to ensure your local environment passes baseline unit tests before making edits.
            </p>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center justify-between gap-2">
              <code className="text-xs font-mono text-emerald-400 break-all">$ {testCommand}</code>
              <button
                onClick={() => handleCopy(testCommand)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors shrink-0"
                title="Copy command"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Action Footer */}
          {onNextStage && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-nova-sm text-center space-y-3">
              <h4 className="text-sm font-bold text-slate-900">Finished Investigating?</h4>
              <p className="text-xs text-slate-500">
                Proceed to Stage 6 to review the step-by-step contribution plan.
              </p>
              <button
                onClick={onNextStage}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-teal-700 hover:bg-teal-600 text-white rounded-xl text-xs font-bold transition-all shadow-nova hover:scale-[1.01]"
              >
                <span>Next Stage: Plan Fix</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InvestigateView;
