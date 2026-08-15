import React, { useState } from 'react';
import { BookOpen, GraduationCap, ChevronDown, ChevronUp, ArrowRight, Lightbulb } from 'lucide-react';

export const LearnConceptsView = ({ issue, onNextStage }) => {
  if (!issue) return null;

  const explanation = issue.explanation || {};
  const structuredConcepts = explanation.structured_concepts || [];

  const [expandedIndex, setExpandedIndex] = useState(0);

  const toggleExpand = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="text-xs font-mono font-bold text-emerald-600 uppercase tracking-wider">
          Stage 3 — Learn Concepts
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight mt-1">
          Prerequisite Technical Concepts
        </h1>
        <p className="text-xs text-gray-500 mt-1">
          Master these core technical concepts before inspecting code or writing unit tests for issue #{issue.github_issue_number}.
        </p>
      </div>

      {/* Structured Concept Cards */}
      <div className="space-y-4">
        {structuredConcepts.length > 0 ? (
          structuredConcepts.map((concept, idx) => {
            const isOpen = expandedIndex === idx;
            return (
              <div 
                key={idx}
                className={`bg-white border rounded-2xl transition-all duration-200 shadow-nova-sm overflow-hidden ${
                  isOpen ? 'border-emerald-400 ring-1 ring-emerald-200' : 'border-gray-200/90 hover:border-gray-300'
                }`}
              >
                {/* Accordion Header */}
                <button
                  onClick={() => toggleExpand(idx)}
                  className="w-full flex items-center justify-between p-5 text-left bg-white hover:bg-gray-50/80 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-100 font-bold text-xs">
                      {idx + 1}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900">{concept.concept_name}</h3>
                      <span className="text-xs text-gray-500 line-clamp-1">{concept.short_explanation}</span>
                    </div>
                  </div>
                  {isOpen ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                </button>

                {/* Accordion Content */}
                {isOpen && (
                  <div className="px-5 pb-5 pt-2 border-t border-gray-100 space-y-4 bg-slate-50/50">
                    {/* What is it? */}
                    <div className="bg-white p-4 rounded-xl border border-gray-100 space-y-1">
                      <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-emerald-600" /> What is it?
                      </div>
                      <p className="text-xs text-gray-700 leading-relaxed font-medium">
                        {concept.short_explanation}
                      </p>
                    </div>

                    {/* Why does it matter? */}
                    <div className="bg-white p-4 rounded-xl border border-gray-100 space-y-1">
                      <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                        <GraduationCap className="w-3.5 h-3.5 text-emerald-600" /> Why does it matter?
                      </div>
                      <p className="text-xs text-gray-700 leading-relaxed font-medium">
                        {concept.why_it_matters}
                      </p>
                    </div>

                    {/* How does it connect to THIS issue? */}
                    <div className="bg-emerald-50/80 p-4 rounded-xl border border-emerald-200/80 space-y-1">
                      <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                        <Lightbulb className="w-3.5 h-3.5 text-emerald-600" /> Connection to Issue #{issue.github_issue_number}
                      </div>
                      <p className="text-xs text-emerald-950 leading-relaxed font-semibold">
                        {concept.connection_to_issue}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="p-6 bg-white border border-gray-200 rounded-2xl text-center">
            <p className="text-xs text-gray-500">General software architecture concepts apply to this issue.</p>
          </div>
        )}
      </div>

      {/* Action Footer */}
      {onNextStage && (
        <div className="flex justify-end pt-4">
          <button
            onClick={onNextStage}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-nova-sm"
          >
            Next Stage: Explore Code →
          </button>
        </div>
      )}
    </div>
  );
};

export default LearnConceptsView;
