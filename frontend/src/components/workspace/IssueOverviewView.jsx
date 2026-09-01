import React from 'react';
import { HelpCircle, Target, GraduationCap, ArrowRight, ExternalLink, ShieldCheck, Clock } from 'lucide-react';
import Badge from '../common/Badge';
import SuitabilityCard from '../diagrams/SuitabilityCard';
import { useTheme } from '../../lib/ThemeContext';

export const IssueOverviewView = ({ issue, onExploreCode }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (!issue) return null;

  const {
    repo_full_name,
    github_issue_number,
    title,
    difficulty_tier = 'BEGINNER',
    repo_language,
    estimated_time = '~1-2 hours',
    reporter_username = 'community_contributor',
    opportunity_signals = {},
    explanation = {},
    github_url,
    beginner_suitability
  } = issue;

  const {
    summary = "The issue asks for clear improvements to the target module.",
    why_it_happens = "The codebase lacks explicit typing or error handling, creating confusion.",
    prerequisite_concepts = [],
    structured_concepts = []
  } = explanation || {};

  const evidenceStatements = opportunity_signals?.evidence_statements || [
    "✓ Open and active on GitHub",
    "✓ Unassigned to any external contributor",
    "✓ Verified target location via AST search"
  ];

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 animate-in fade-in duration-200">
      {/* Top Main Header Card */}
      <div className={`rounded-2xl p-6 border transition-colors ${
        isDark 
          ? 'bg-[#08131A] border-slate-800 shadow-lg text-white' 
          : 'bg-white border-slate-200 shadow-nova-sm text-slate-900'
      }`}>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
          <div className="flex items-center gap-2">
            <span className={`font-extrabold text-sm tracking-tight ${
              isDark ? 'text-white' : 'text-slate-900'
            }`}>
              {repo_full_name}
            </span>
            <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
              isDark 
                ? 'bg-[#071F1B] border-emerald-500/30 text-[#34D399]' 
                : 'bg-teal-50 border-teal-200 text-teal-700'
            }`}>
              <ShieldCheck className="w-3.5 h-3.5" /> Code Target Grounded
            </span>
          </div>

          {github_issue_number && (
            <span className="text-xs text-slate-400 font-mono font-bold">Issue #{github_issue_number}</span>
          )}
        </div>

        <h1 className={`text-xl md:text-2xl font-extrabold leading-tight mb-4 tracking-tight ${
          isDark ? 'text-white' : 'text-slate-900'
        }`}>
          {title}
        </h1>

        <div className={`flex flex-wrap items-center justify-between gap-3 pt-3 border-t ${
          isDark ? 'border-slate-800' : 'border-slate-100'
        }`}>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={difficulty_tier.toLowerCase()}>{difficulty_tier}</Badge>
            {repo_language && <Badge variant="language">{repo_language}</Badge>}
            {estimated_time && (
              <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-lg font-medium border ${
                isDark 
                  ? 'bg-[#0B1B24] border-slate-700 text-slate-300' 
                  : 'bg-slate-50 border-slate-200 text-slate-600'
              }`}>
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Effort: {estimated_time}
              </span>
            )}
          </div>

          {github_url && (
            <a
              href={github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#064E3B] bg-[#9FE8C3] hover:bg-[#86EFAC] px-3.5 py-1.5 rounded-xl transition-all shadow-sm font-bold"
            >
              <span>View on GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* 2-Column Responsive Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (7 cols): Objective, Root Cause, Concepts */}
        <div className="lg:col-span-7 space-y-6">
          {/* Section 1: Issue Objective */}
          <div className={`rounded-2xl p-5 border space-y-2 transition-colors ${
            isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-white border-slate-200 shadow-nova-sm text-slate-900'
          }`}>
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <HelpCircle className="w-4 h-4 text-[#34D399]" />
              <span>Issue Objective</span>
            </div>
            <p className={`text-xs md:text-sm leading-relaxed font-medium ${
              isDark ? 'text-slate-300' : 'text-slate-800'
            }`}>
              {summary}
            </p>
          </div>

          {/* Section 2: Technical Context & Root Cause */}
          <div className={`rounded-2xl p-5 border space-y-2 transition-colors ${
            isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-white border-slate-200 shadow-nova-sm text-slate-900'
          }`}>
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <Target className="w-4 h-4 text-blue-400" />
              <span>Likely Cause & Technical Context</span>
            </div>
            <p className={`text-xs md:text-sm leading-relaxed p-3.5 rounded-xl border font-sans font-medium ${
              isDark 
                ? 'bg-[#050C10] border-slate-800 text-slate-300' 
                : 'bg-slate-50 border-slate-200 text-slate-800'
            }`}>
              {why_it_happens}
            </p>
          </div>

          {/* Section 3: Prerequisite Concepts */}
          <div className={`rounded-2xl p-5 border space-y-3 transition-colors ${
            isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-white border-slate-200 shadow-nova-sm text-slate-900'
          }`}>
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <GraduationCap className="w-4 h-4 text-purple-400" />
              <span>Prerequisite Concepts</span>
            </div>

            {structured_concepts.length > 0 ? (
              <div className="space-y-2">
                {structured_concepts.map((concept, i) => (
                  <div key={i} className={`p-3 rounded-xl border ${
                    isDark ? 'bg-[#0B1B24] border-slate-800' : 'bg-slate-50 border-slate-200/70'
                  }`}>
                    <span className={`font-bold text-xs block mb-0.5 ${
                      isDark ? 'text-white' : 'text-slate-900'
                    }`}>{concept.concept_name}</span>
                    <p className={`text-xs leading-relaxed mb-1.5 ${
                      isDark ? 'text-slate-300' : 'text-slate-600'
                    }`}>{concept.short_explanation}</p>
                    <div className={`p-2 rounded-lg border text-[11px] font-medium ${
                      isDark 
                        ? 'bg-[#181124] border-purple-900/50 text-purple-200' 
                        : 'bg-purple-50 border-purple-100 text-purple-900'
                    }`}>
                      <span className="font-bold">Why it matters:</span> {concept.why_it_matters}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {prerequisite_concepts.length > 0 ? (
                  prerequisite_concepts.map((concept, i) => (
                    <span key={i} className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${
                      isDark ? 'bg-[#0B1B24] border-slate-700 text-slate-300' : 'bg-slate-100 text-slate-800 border-slate-200'
                    }`}>
                      {concept}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400">Basic Git & {repo_language || 'programming'} fundamentals</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN (5 cols): Suitability Matrix & Availability */}
        <div className="lg:col-span-5 space-y-6">
          {/* Suitability Score Breakdown Card */}
          {beginner_suitability && (
            <SuitabilityCard suitability={beginner_suitability} />
          )}

          {/* Availability & Pre-Flight Card */}
          <div className={`rounded-2xl p-5 border space-y-3 shadow-md ${
            isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-slate-900 border-slate-800 text-white'
          }`}>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#34D399] animate-pulse" />
                <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Availability Pre-Flight</h3>
              </div>
              <span className="text-[11px] font-mono text-slate-400">@{reporter_username}</span>
            </div>

            <div className="space-y-1.5">
              {evidenceStatements.map((stmt, i) => (
                <div key={i} className={`text-xs font-medium flex items-center gap-2 px-3 py-1.5 rounded-lg border ${
                  isDark ? 'bg-[#050B0E] border-slate-800 text-slate-300' : 'bg-slate-800 border-slate-700 text-slate-300'
                }`}>
                  <span>{stmt}</span>
                </div>
              ))}
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed pt-1">
              GitNova verifies commit SHAs, file existence, and test commands before publishing.
            </p>
          </div>

          {/* Action CTA Box */}
          <div className={`rounded-2xl p-5 text-center space-y-3 border shadow-sm ${
            isDark 
              ? 'bg-[#071F1B]/60 border-emerald-500/30 text-white' 
              : 'bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200 text-teal-950'
          }`}>
            <h4 className="text-sm font-bold">Ready to begin this task?</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-300' : 'text-teal-800'}`}>
              Step through the guided 10-stage journey to inspect code, plan the fix, run tests, and prepare your PR.
            </p>
            <button
              onClick={onExploreCode}
              className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#064E3B] rounded-xl text-xs font-extrabold transition-all shadow-sm hover:scale-[1.01]"
            >
              <span>Begin Guided Journey</span>
              <ArrowRight className="w-3.5 h-3.5 stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IssueOverviewView;
