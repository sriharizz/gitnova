import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Brain, FileCode, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw,
  BookOpen, ListOrdered, Layers, ExternalLink, ShieldCheck
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function GroundedIssueExplanationView({ repoName, issueTitle, issueBody, commitSha, initialData = null }) {
  const [explanation, setExplanation] = useState(initialData);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState(null);

  const fetchExplanation = async () => {
    try {
      setLoading(true);
      setError(null);

      const payload = {
        repo_name: repoName,
        issue_title: issueTitle,
        issue_body: issueBody || '',
        commit_sha: commitSha || null,
      };

      const response = await axios.post(`${API_BASE_URL}/issues/explain`, payload, {
        timeout: 60000,
      });

      setExplanation(response.data);
    } catch (err) {
      console.error('[GitNova] Issue Explanation fetch error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to generate grounded issue explanation.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialData && (repoName || issueTitle)) {
      fetchExplanation();
    }
  }, [repoName, issueTitle, commitSha]);

  if (loading) {
    return (
      <div className="p-6 bg-[#0f172a]/90 rounded-2xl border border-slate-700/80 shadow-2xl space-y-5 animate-pulse">
        <div className="flex items-center gap-3 border-b border-slate-700/60 pb-4">
          <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400">
            <Brain className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <div className="h-4 w-48 bg-slate-700 rounded mb-1"></div>
            <div className="h-3 w-72 bg-slate-800 rounded"></div>
          </div>
        </div>
        <div className="space-y-3">
          <div className="h-16 bg-slate-800/60 rounded-xl"></div>
          <div className="h-24 bg-slate-800/40 rounded-xl"></div>
          <div className="h-20 bg-slate-800/50 rounded-xl"></div>
        </div>
        <p className="text-xs font-mono text-center text-violet-400">
          Running Sprint 7 Hybrid Retrieval & LLM Grounding Verifier...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-950/20 rounded-2xl border border-red-900/40 text-red-300 space-y-4">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-6 h-6 text-red-400 shrink-0" />
          <h3 className="font-bold text-base text-red-200">Could Not Generate Explanation</h3>
        </div>
        <p className="text-xs text-red-300/80 font-mono leading-relaxed">{error}</p>
        <button
          onClick={fetchExplanation}
          className="inline-flex items-center gap-2 px-4 py-2 bg-red-900/40 hover:bg-red-900/60 border border-red-700/50 text-red-200 rounded-lg text-xs font-mono font-semibold transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retry Analysis
        </button>
      </div>
    );
  }

  if (!explanation) return null;

  if (explanation.status === 'INSUFFICIENT_EVIDENCE') {
    return (
      <div className="p-6 bg-amber-950/20 rounded-2xl border border-amber-900/50 text-amber-300 space-y-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0" />
          <div>
            <h3 className="font-bold text-sm text-amber-200 uppercase tracking-wider font-mono">GitNova couldn't verify this yet</h3>
            <p className="text-xs text-amber-300/90 mt-0.5">{explanation.why_it_happens || explanation.summary}</p>
          </div>
        </div>
        <p className="text-xs text-amber-400/80 font-mono leading-relaxed bg-amber-950/40 p-3 rounded-lg border border-amber-900/30">
          {explanation.disclaimer || 'GitNova skips automated generation when retrieved codebase context is insufficient to prevent hallucinations.'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-sans">
      {/* Disclaimer Notice Banner */}
      {explanation.disclaimer && (
        <div className="p-3 bg-indigo-950/40 border border-indigo-800/40 rounded-xl text-indigo-300 text-xs font-mono flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <span>{explanation.disclaimer}</span>
        </div>
      )}

      {/* Section 1: What This Issue Means */}
      <div className="bg-[#131d31] rounded-2xl border border-slate-700/80 overflow-hidden shadow-xl">
        <div className="px-5 py-3 bg-[#1c283e] border-b border-slate-700/80 flex items-center gap-2.5">
          <BookOpen className="w-4 h-4 text-violet-400" />
          <span className="text-xs font-bold text-violet-300 uppercase tracking-widest font-mono">1. What This Issue Means</span>
        </div>
        <div className="p-5 text-slate-200 text-sm leading-relaxed prose prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation.summary}</ReactMarkdown>
        </div>
      </div>

      {/* Section 2: Why This Happens */}
      <div className="bg-[#131d31] rounded-2xl border border-slate-700/80 overflow-hidden shadow-xl">
        <div className="px-5 py-3 bg-[#1c283e] border-b border-slate-700/80 flex items-center gap-2.5">
          <Brain className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-indigo-300 uppercase tracking-widest font-mono">2. Why This Happens (Root Cause)</span>
        </div>
        <div className="p-5 text-slate-200 text-sm leading-relaxed prose prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{explanation.why_it_happens}</ReactMarkdown>
        </div>
      </div>

      {/* Section 3: What To Understand First */}
      {explanation.prerequisite_concepts && explanation.prerequisite_concepts.length > 0 && (
        <div className="bg-[#131d31] rounded-2xl border border-slate-700/80 overflow-hidden shadow-xl">
          <div className="px-5 py-3 bg-[#1c283e] border-b border-slate-700/80 flex items-center gap-2.5">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-bold text-emerald-300 uppercase tracking-widest font-mono">3. What To Understand First</span>
          </div>
          <div className="p-5 flex flex-wrap gap-2">
            {explanation.prerequisite_concepts.map((concept, idx) => (
              <div key={idx} className="px-3 py-1.5 bg-emerald-950/40 border border-emerald-800/50 rounded-lg text-emerald-300 text-xs font-mono flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                {concept}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 4: Step-by-Step Solution */}
      {explanation.step_by_step_plan && explanation.step_by_step_plan.length > 0 && (
        <div className="bg-[#131d31] rounded-2xl border border-slate-700/80 overflow-hidden shadow-xl">
          <div className="px-5 py-3 bg-[#1c283e] border-b border-slate-700/80 flex items-center gap-2.5">
            <ListOrdered className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-cyan-300 uppercase tracking-widest font-mono">4. Step-by-Step Solution</span>
          </div>
          <div className="p-5 space-y-4">
            {explanation.step_by_step_plan.map((step, idx) => (
              <div key={idx} className="p-4 bg-[#1a253a] rounded-xl border border-slate-700/60 flex items-start gap-4">
                <div className="w-7 h-7 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                  {step.step_number || idx + 1}
                </div>
                <div className="flex-1 space-y-1">
                  <h4 className="text-sm font-bold text-white">{step.title}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed">{step.description}</p>
                  {step.target_file && (
                    <div className="pt-1">
                      <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-900/50 inline-block">
                        Target File: {step.target_file}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 5: Relevant Files / Symbols / Lines */}
      {explanation.relevant_locations && explanation.relevant_locations.length > 0 && (
        <div className="bg-[#131d31] rounded-2xl border border-slate-700/80 overflow-hidden shadow-xl">
          <div className="px-5 py-3 bg-[#1c283e] border-b border-slate-700/80 flex items-center gap-2.5">
            <FileCode className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-bold text-purple-300 uppercase tracking-widest font-mono">5. Relevant Files, Symbols & Lines</span>
          </div>
          <div className="p-5 divide-y divide-slate-800">
            {explanation.relevant_locations.map((loc, idx) => (
              <div key={idx} className="py-3 first:pt-0 last:pb-0 flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-purple-300">{loc.file_path}</span>
                    {loc.is_verified && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/60">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Verified Code
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 font-mono">
                    {loc.symbol_name && <span className="mr-3">Symbol: <code className="text-purple-200 bg-purple-950/40 px-1 py-0.5 rounded border border-purple-900/40">{loc.symbol_name}</code></span>}
                    {loc.lines && <span>Lines: <code className="text-slate-300">{loc.lines}</code></span>}
                  </div>
                </div>
                {loc.role && (
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider bg-slate-800 px-2 py-1 rounded border border-slate-700 shrink-0 self-start md:self-auto">
                    {loc.role}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 6: Common Pitfalls */}
      {explanation.common_pitfalls && explanation.common_pitfalls.length > 0 && (
        <div className="bg-[#131d31] rounded-2xl border border-slate-700/80 overflow-hidden shadow-xl">
          <div className="px-5 py-3 bg-[#1c283e] border-b border-slate-700/80 flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span className="text-xs font-bold text-rose-300 uppercase tracking-widest font-mono">6. Common Pitfalls & Considerations</span>
          </div>
          <div className="p-5 space-y-2.5">
            {explanation.common_pitfalls.map((pitfall, idx) => (
              <div key={idx} className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-xl text-rose-200 text-xs font-mono flex items-start gap-2.5">
                <span className="text-rose-400 font-bold shrink-0">!</span>
                <span className="leading-relaxed">{pitfall}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
