import React from 'react';
import { CheckCircle2, AlertTriangle, Layers, Wrench, Shield, Compass } from 'lucide-react';
import ProvenanceBadge from './ProvenanceBadge';
import { useTheme } from '../../lib/ThemeContext';

const TIER_CONFIG = {
  BEGINNER: { label: 'Beginner Friendly', color: 'text-emerald-700 bg-emerald-50/90 border-emerald-300 ring-1 ring-emerald-500/20' },
  BEGINNER_PLUS: { label: 'Beginner Plus', color: 'text-teal-700 bg-teal-50/90 border-teal-300 ring-1 ring-teal-500/20' },
  INTERMEDIATE: { label: 'Intermediate', color: 'text-blue-700 bg-blue-50/90 border-blue-300 ring-1 ring-blue-500/20' },
  ADVANCED: { label: 'Advanced', color: 'text-purple-700 bg-purple-50/90 border-purple-300 ring-1 ring-purple-500/20' }
};

function formatPillarValue(val) {
  if (!val) return 'Standard';
  const str = String(val).toUpperCase();
  if (str === 'DOCUMENTATION' || str === 'DOC_FIX') return 'Docs / Text';
  if (str === 'BUG_FIX') return 'Bug Fix';
  if (str === 'SMALL_FEATURE') return 'Small Feature';
  if (str === 'FEATURE') return 'Feature';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase().replace(/_/g, ' ');
}

export default function SuitabilityCard({ suitability, className = '' }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (!suitability) return null;

  const {
    score = 75,
    tier = 'BEGINNER',
    repository_complexity = 'MEDIUM',
    contribution_complexity = 'BEGINNER',
    setup_complexity = 'EASY',
    contribution_type = 'BUG_FIX',
    positive_signals = [],
    warning_signals = []
  } = suitability;

  const tierInfo = TIER_CONFIG[tier] || TIER_CONFIG.BEGINNER;

  // Normalized complexity percent for visual progress bars
  const getPillarPercent = (val) => {
    const s = String(val).toUpperCase();
    if (s === 'EASY' || s === 'BEGINNER' || s === 'LOW' || s === 'DOC_FIX' || s === 'DOCUMENTATION') return 95;
    if (s === 'MEDIUM' || s === 'BUG_FIX' || s === 'MODERATE' || s === 'SMALL_FEATURE') return 75;
    if (s === 'HARD' || s === 'HIGH' || s === 'FEATURE' || s === 'ADVANCED') return 45;
    return 80;
  };

  return (
    <div className={`rounded-2xl border p-5 space-y-4 transition-colors ${
      isDark 
        ? 'bg-[#08131A] border-slate-800 shadow-lg text-white' 
        : 'bg-white border-slate-200/90 shadow-nova-sm text-slate-900'
    } ${className}`}>
      
      {/* Top Header Row with Score Dial, Tier Badge & Provenance */}
      <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b ${
        isDark ? 'border-slate-800' : 'border-slate-100'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`relative w-11 h-11 rounded-xl flex flex-col items-center justify-center border shadow-sm shrink-0 ${
            isDark ? 'bg-[#060F14] border-slate-700 text-white' : 'bg-slate-900 border-slate-800 text-white'
          }`}>
            <span className="text-base font-extrabold font-mono text-[#34D399] leading-none">{score}</span>
            <span className="text-[9px] font-mono text-slate-400 tracking-tighter">/100</span>
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h4 className={`text-xs font-bold uppercase tracking-wider ${
                isDark ? 'text-white' : 'text-slate-900'
              }`}>
                Beginner Suitability
              </h4>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                isDark 
                  ? 'bg-[#071F1B] border-emerald-500/30 text-[#34D399]' 
                  : tierInfo.color
              }`}>
                {tierInfo.label}
              </span>
            </div>
            <p className={`text-[11px] font-medium mt-0.5 ${
              isDark ? 'text-slate-400' : 'text-slate-500'
            }`}>
              Code scope, repository size & setup complexity
            </p>
          </div>
        </div>

        <ProvenanceBadge type="AI_INFERENCE" source="Suitability Analysis" className="self-start sm:self-center" />
      </div>

      {/* 4 Clean Decoupled Complexity Pillars */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Pillar 1: Repo Scope */}
        <div className={`p-2.5 sm:p-3 rounded-xl border flex flex-col justify-between min-h-[78px] ${
          isDark ? 'bg-[#0B1B24] border-slate-800' : 'bg-slate-50 border-slate-200/70'
        }`}>
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Layers className="w-3.5 h-3.5 text-teal-400 shrink-0" />
              <span className="text-[10px] font-bold uppercase tracking-wider truncate">Repo Size</span>
            </div>
            <div className={`text-xs font-bold truncate ${
              isDark ? 'text-slate-200' : 'text-slate-800'
            }`}>
              {formatPillarValue(repository_complexity)}
            </div>
          </div>
          <div className={`w-full h-1.5 rounded-full overflow-hidden mt-2 ${
            isDark ? 'bg-slate-800' : 'bg-slate-200'
          }`}>
            <div className="h-full bg-teal-500 rounded-full" style={{ width: `${getPillarPercent(repository_complexity)}%` }} />
          </div>
        </div>

        {/* Pillar 2: Contribution Scope */}
        <div className={`p-2.5 sm:p-3 rounded-xl border flex flex-col justify-between min-h-[78px] ${
          isDark ? 'bg-[#0B1B24] border-slate-800' : 'bg-slate-50 border-slate-200/70'
        }`}>
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Compass className="w-3.5 h-3.5 text-[#34D399] shrink-0" />
              <span className="text-[10px] font-bold uppercase tracking-wider truncate">Code Scope</span>
            </div>
            <div className={`text-xs font-bold truncate ${
              isDark ? 'text-slate-200' : 'text-slate-800'
            }`}>
              {formatPillarValue(contribution_complexity)}
            </div>
          </div>
          <div className={`w-full h-1.5 rounded-full overflow-hidden mt-2 ${
            isDark ? 'bg-slate-800' : 'bg-slate-200'
          }`}>
            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${getPillarPercent(contribution_complexity)}%` }} />
          </div>
        </div>

        {/* Pillar 3: Environment Setup */}
        <div className={`p-2.5 sm:p-3 rounded-xl border flex flex-col justify-between min-h-[78px] ${
          isDark ? 'bg-[#0B1B24] border-slate-800' : 'bg-slate-50 border-slate-200/70'
        }`}>
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Wrench className="w-3.5 h-3.5 text-blue-400 shrink-0" />
              <span className="text-[10px] font-bold uppercase tracking-wider truncate">Env Setup</span>
            </div>
            <div className={`text-xs font-bold truncate ${
              isDark ? 'text-slate-200' : 'text-slate-800'
            }`}>
              {formatPillarValue(setup_complexity)}
            </div>
          </div>
          <div className={`w-full h-1.5 rounded-full overflow-hidden mt-2 ${
            isDark ? 'bg-slate-800' : 'bg-slate-200'
          }`}>
            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${getPillarPercent(setup_complexity)}%` }} />
          </div>
        </div>

        {/* Pillar 4: Task Type */}
        <div className={`p-2.5 sm:p-3 rounded-xl border flex flex-col justify-between min-h-[78px] ${
          isDark ? 'bg-[#0B1B24] border-slate-800' : 'bg-slate-50 border-slate-200/70'
        }`}>
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Shield className="w-3.5 h-3.5 text-purple-400 shrink-0" />
              <span className="text-[10px] font-bold uppercase tracking-wider truncate">Task Type</span>
            </div>
            <div className={`text-xs font-bold truncate ${
              isDark ? 'text-slate-200' : 'text-slate-800'
            }`}>
              {formatPillarValue(contribution_type)}
            </div>
          </div>
          <div className={`w-full h-1.5 rounded-full overflow-hidden mt-2 ${
            isDark ? 'bg-slate-800' : 'bg-slate-200'
          }`}>
            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${getPillarPercent(contribution_type)}%` }} />
          </div>
        </div>
      </div>

      {/* Verified Signals Checklist */}
      {(positive_signals.length > 0 || warning_signals.length > 0) && (
        <div className={`pt-3 border-t ${
          isDark ? 'border-slate-800' : 'border-slate-100'
        }`}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs items-stretch">
            {positive_signals.map((sig, idx) => (
              <div 
                key={idx} 
                className={`flex items-center gap-2 px-3 py-2 rounded-xl border font-medium ${
                  isDark 
                    ? 'bg-[#0B1B24] border-slate-800 text-slate-200' 
                    : 'bg-slate-50 border-slate-200/70 text-slate-700'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-[#34D399] shrink-0" />
                <span className="text-[11px] leading-tight truncate">{sig.replace(/^✓\s*/, '')}</span>
              </div>
            ))}
            {warning_signals.map((warn, idx) => (
              <div 
                key={idx} 
                className={`flex items-center gap-2 px-3 py-2 rounded-xl border font-medium ${
                  isDark 
                    ? 'bg-amber-950/30 border-amber-900/50 text-amber-200' 
                    : 'bg-amber-50 border-amber-200 text-amber-900'
                }`}
              >
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                <span className="text-[11px] leading-tight truncate">{warn.replace(/^⚠\s*/, '')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
