import React, { useState } from 'react';
import { BookOpen, GraduationCap, ChevronDown, ChevronUp, ArrowRight, Lightbulb } from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';

export const LearnConceptsView = ({ issue, onNextStage }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (!issue) return null;

  const explanation = issue.explanation || {};
  
  // Normalize concepts from structured_concepts, prerequisite_concepts, or concepts
  const rawConcepts = explanation.structured_concepts || explanation.prerequisite_concepts || explanation.concepts || [];
  const structuredConcepts = Array.isArray(rawConcepts)
    ? rawConcepts.map((item, idx) => {
        if (typeof item === 'string') {
          return {
            concept_name: item,
            short_explanation: `Understanding the architectural conventions and standard library behaviors associated with ${item.toLowerCase()}.`,
            why_it_matters: `Ensures the proposed change adheres to existing repository conventions without introducing unexpected edge-case regressions.`,
            connection_to_issue: `Directly relevant to analyzing and fixing the issue reported in #${issue.github_issue_number}.`
          };
        }
        return item;
      })
    : [];

  const [expandedIndex, setExpandedIndex] = useState(0);

  const toggleExpand = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="max-w-4xl mx-auto p-3 sm:p-6 lg:p-8 space-y-4 sm:space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className={`border-b pb-4 transition-colors ${
        isDark ? 'border-slate-800' : 'border-slate-200'
      }`}>
        <div className="text-xs font-mono font-bold text-[#34D399] uppercase tracking-wider">
          Stage 03 — Learn Concepts
        </div>
        <h1 className={`text-xl sm:text-2xl font-extrabold tracking-tight mt-1 ${
          isDark ? 'text-white' : 'text-slate-900'
        }`}>
          Prerequisite Technical Concepts
        </h1>
        <p className={`text-xs mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
          Review these foundational technical concepts before inspecting code or writing unit tests for issue #{issue.github_issue_number}.
        </p>
      </div>

      {/* Structured Concept Cards */}
      <div className="space-y-3 sm:space-y-4">
        {structuredConcepts.length > 0 ? (
          structuredConcepts.map((concept, idx) => {
            const isOpen = expandedIndex === idx;
            return (
              <div 
                key={idx}
                className={`border rounded-2xl transition-all duration-200 shadow-nova-sm overflow-hidden ${
                  isOpen 
                    ? (isDark ? 'border-emerald-500/40 bg-[#08131A] ring-1 ring-emerald-500/20' : 'border-emerald-400 ring-1 ring-emerald-200 bg-white')
                    : (isDark ? 'border-slate-800 bg-[#08131A] hover:border-slate-700' : 'border-slate-200/90 hover:border-slate-300 bg-white')
                }`}
              >
                {/* Accordion Header */}
                <button
                  onClick={() => toggleExpand(idx)}
                  className={`w-full flex items-center justify-between p-4 sm:p-5 text-left transition-colors ${
                    isDark ? 'hover:bg-slate-800/40' : 'hover:bg-gray-50/80'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border font-bold text-xs ${
                      isDark 
                        ? 'bg-[#071F1B] text-[#34D399] border-emerald-500/30' 
                        : 'bg-emerald-50 text-emerald-600 border-emerald-100'
                    }`}>
                      {idx + 1}
                    </div>
                    <div className="min-w-0">
                      <h3 className={`text-sm sm:text-base font-bold truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {concept.concept_name}
                      </h3>
                      <span className={`text-xs block truncate ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        {concept.short_explanation}
                      </span>
                    </div>
                  </div>
                  {isOpen ? <ChevronUp className="w-5 h-5 text-slate-400 shrink-0 ml-2" /> : <ChevronDown className="w-5 h-5 text-slate-400 shrink-0 ml-2" />}
                </button>

                {/* Accordion Content */}
                {isOpen && (
                  <div className={`px-4 sm:px-5 pb-5 pt-2 border-t space-y-3 sm:space-y-4 ${
                    isDark ? 'border-slate-800 bg-[#040C11]' : 'border-slate-100 bg-slate-50/50'
                  }`}>
                    {/* What is it? */}
                    <div className={`p-3.5 sm:p-4 rounded-xl border space-y-1 ${
                      isDark ? 'bg-[#08131A] border-slate-800' : 'bg-white border-slate-100'
                    }`}>
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-[#34D399]" /> What is it?
                      </div>
                      <p className={`text-xs leading-relaxed font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        {concept.short_explanation}
                      </p>
                    </div>

                    {/* Why does it matter? */}
                    <div className={`p-3.5 sm:p-4 rounded-xl border space-y-1 ${
                      isDark ? 'bg-[#08131A] border-slate-800' : 'bg-white border-slate-100'
                    }`}>
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <GraduationCap className="w-3.5 h-3.5 text-[#34D399]" /> Why does it matter?
                      </div>
                      <p className={`text-xs leading-relaxed font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        {concept.why_it_matters}
                      </p>
                    </div>

                    {/* How does it connect to THIS issue? */}
                    <div className={`p-3.5 sm:p-4 rounded-xl border space-y-1 ${
                      isDark 
                        ? 'bg-[#071F1B] border-emerald-500/30 text-emerald-200' 
                        : 'bg-emerald-50/80 border-emerald-200/80 text-emerald-950'
                    }`}>
                      <div className={`text-[11px] font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                        isDark ? 'text-[#34D399]' : 'text-emerald-800'
                      }`}>
                        <Lightbulb className="w-3.5 h-3.5 text-[#34D399]" /> Connection to Issue #{issue.github_issue_number}
                      </div>
                      <p className="text-xs leading-relaxed font-semibold">
                        {concept.connection_to_issue}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className={`p-6 border rounded-2xl text-center ${
            isDark ? 'bg-[#08131A] border-slate-800 text-slate-400' : 'bg-white border-slate-200 text-slate-500'
          }`}>
            <p className="text-xs">Prerequisite concept guidance is not explicitly specified for this issue. You can proceed directly to exploring the code context.</p>
          </div>
        )}
      </div>

      {/* Action Footer */}
      {onNextStage && (
        <div className="flex justify-end pt-4">
          <button
            onClick={onNextStage}
            className="w-full sm:w-auto px-5 py-2.5 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#064E3B] rounded-xl text-xs font-extrabold transition-all shadow-sm flex items-center justify-center gap-1.5"
          >
            <span>Next: Explore Code</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
};

export default LearnConceptsView;
