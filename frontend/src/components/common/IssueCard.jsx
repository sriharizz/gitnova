import React, { useState } from 'react';
import { ArrowRight, Star, Sparkles, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';

const LANG_COLORS = {
  Python: '#3776AB',
  JavaScript: '#F7DF1E',
  TypeScript: '#3178C6',
  Go: '#00ADD8',
  Rust: '#DEA584',
  Java: '#B07219',
  'C++': '#F34B7D'
};

/**
 * Extracts clean, human-readable summary text from raw AI summary / JSON payload strings.
 */
function getCleanSummary(raw) {
  if (!raw) return "Verified open-source issue with complete AST-guided resolution plan.";
  
  if (typeof raw === 'object') {
    return raw.summary || raw.ai_hint || raw.explanation || raw.why_it_happens || JSON.stringify(raw);
  }
  
  if (typeof raw === 'string') {
    const trimmed = raw.trim();
    if (trimmed.startsWith('{')) {
      try {
        const parsed = JSON.parse(trimmed);
        if (parsed.summary) return parsed.summary;
        if (parsed.ai_hint) return parsed.ai_hint;
        if (parsed.explanation) return parsed.explanation;
        if (parsed.why_it_happens) return parsed.why_it_happens;
      } catch {
        // Regex extraction fallback for JSON-like string
        const summaryMatch = trimmed.match(/"summary":\s*"([^"\\]*(?:\\.[^"\\]*)*)"/);
        if (summaryMatch && summaryMatch[1]) {
          return summaryMatch[1].replace(/\\"/g, '"');
        }
      }
    }
    return trimmed;
  }
  
  return String(raw);
}

export const IssueCard = ({ issue, onSelect }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    id,
    repo_full_name,
    title,
    ai_hint,
    ai_summary_preview,
    summary,
    difficulty_tier = 'BEGINNER',
    repo_language,
    repo_stars,
    reporter_username = 'community_contributor',
    verification_status = 'VERIFIED',
    availability_status = 'LIKELY_AVAILABLE',
    beginner_suitability
  } = issue;

  const repoOwner = repo_full_name ? repo_full_name.split('/')[0] : 'github';
  const avatarUrl = `https://github.com/${repoOwner}.png`;

  const suitabilityScore = beginner_suitability?.score ?? issue.quality_score ?? 85;
  const contribType = beginner_suitability?.contribution_type || 'BUG_FIX';
  const contribTier = beginner_suitability?.contribution_complexity || difficulty_tier;
  const langColor = LANG_COLORS[repo_language] || '#10B981';

  const previewText = getCleanSummary(ai_hint || ai_summary_preview || summary);

  return (
    <div
      onClick={() => onSelect(id)}
      className={`rounded-2xl p-5 transition-all duration-200 cursor-pointer group flex flex-col justify-between relative overflow-hidden ${
        isDark 
          ? 'bg-[#08131A]/95 border border-slate-800/90 hover:border-emerald-500/60 shadow-[0_4px_20px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_30px_rgba(16,185,129,0.15)]' 
          : 'bg-white border border-slate-200/90 hover:border-teal-500/80 shadow-nova-sm hover:shadow-card-hover'
      }`}
    >
      {/* Top Accent Gradient on Hover */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-emerald-400 to-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

      <div>
        {/* Header: Repo avatar + name + availability badge */}
        <div className="flex items-start justify-between gap-3 mb-2.5">
          <div className="flex items-center gap-2.5 min-w-0">
            <img
              src={avatarUrl}
              alt={repo_full_name}
              className={`w-7 h-7 rounded-lg border object-cover shrink-0 ${
                isDark ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-slate-50'
              }`}
              onError={(e) => { e.target.src = 'https://github.githubassets.com/favicons/favicon.png'; }}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className={`font-extrabold text-xs truncate tracking-tight ${
                  isDark ? 'text-white' : 'text-slate-900'
                }`}>
                  {repo_full_name}
                </span>
                {verification_status === 'VERIFIED' && (
                  <ShieldCheck className="w-3.5 h-3.5 text-[#34D399] shrink-0" title="Verified by GitNova" />
                )}
              </div>
              <span className={`text-[11px] block truncate font-mono ${
                isDark ? 'text-slate-400' : 'text-slate-400'
              }`}>
                @{reporter_username}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {availability_status === 'LIKELY_AVAILABLE' ? (
              <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                isDark 
                  ? 'text-[#34D399] bg-[#071F1B] border border-emerald-500/30' 
                  : 'text-emerald-700 bg-emerald-50 border border-emerald-200'
              }`}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                AVAILABLE
              </span>
            ) : availability_status === 'CHECK_DISCUSSION' ? (
              <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                isDark 
                  ? 'text-amber-300 bg-amber-950/40 border border-amber-500/30' 
                  : 'text-amber-700 bg-amber-50 border border-amber-200'
              }`}>
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                CHECK DISCUSSION
              </span>
            ) : (
              <span className="text-[10px] font-bold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                UNVERIFIED
              </span>
            )}

            {repo_stars > 0 && (
              <div className={`flex items-center gap-0.5 text-[11px] font-mono font-medium px-1.5 py-0.5 rounded border ${
                isDark ? 'bg-[#0E1C25] border-slate-700 text-slate-300' : 'bg-slate-50 border-slate-100 text-slate-500'
              }`}>
                <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                <span>{repo_stars >= 1000 ? `${(repo_stars / 1000).toFixed(1)}k` : repo_stars}</span>
              </div>
            )}
          </div>
        </div>

        {/* Issue Title */}
        <h3 className={`text-sm font-bold leading-snug mb-2 group-hover:text-[#34D399] transition-colors line-clamp-2 tracking-tight ${
          isDark ? 'text-white' : 'text-slate-900'
        }`}>
          {title}
        </h3>

        {/* Clean Human-Readable Issue Preview with Read More Toggle */}
        <div className="mb-3">
          <p className={`text-xs leading-relaxed transition-colors ${
            isExpanded ? '' : 'line-clamp-2'
          } ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
            {previewText}
          </p>
          
          {previewText.length > 80 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-[#34D399] hover:underline mt-1"
            >
              <span>{isExpanded ? 'Show less' : 'Read more'}</span>
              {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}
        </div>

        {/* Pillar Micro-Chips */}
        <div className="flex flex-wrap gap-1.5 mb-3.5">
          <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border ${
            isDark ? 'bg-[#0D1E28] border-slate-700/80 text-slate-300' : 'bg-slate-50 border-slate-200/70 text-slate-600'
          }`}>
            AST Verified
          </span>
          <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border ${
            isDark ? 'bg-[#0D1E28] border-slate-700/80 text-slate-300' : 'bg-slate-50 border-slate-200/70 text-slate-600'
          }`}>
            Isolated Scope
          </span>
          <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border ${
            isDark ? 'bg-[#0D1E28] border-slate-700/80 text-slate-300' : 'bg-slate-50 border-slate-200/70 text-slate-600'
          }`}>
            {contribType.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Footer Meta & Suitability Score */}
      <div className={`pt-3 border-t flex items-center justify-between gap-2 transition-colors ${
        isDark ? 'border-slate-800' : 'border-slate-100'
      }`}>
        <div className="flex flex-wrap items-center gap-1.5">
          {/* Suitability Score Pill */}
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-mono font-bold border shadow-sm ${
            isDark 
              ? 'bg-[#071F1B] text-[#34D399] border-emerald-500/40' 
              : 'bg-teal-50 text-teal-800 border-teal-200'
          }`}>
            <Sparkles className="w-3 h-3 text-[#34D399]" />
            <span>{suitabilityScore}/100</span>
            <span className="text-[10px] opacity-75 font-sans font-semibold uppercase">· {contribTier.replace('_', '+')}</span>
          </span>

          {/* Language Badge */}
          {repo_language && (
            <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium border ${
              isDark ? 'bg-[#0E1C25] text-slate-300 border-slate-700' : 'bg-slate-100 text-slate-700 border-slate-200'
            }`}>
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: langColor }} />
              {repo_language}
            </span>
          )}
        </div>

        {/* Start Button */}
        <button
          onClick={(e) => { e.stopPropagation(); onSelect(id); }}
          className="inline-flex items-center gap-1 px-3.5 py-1.5 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#064E3B] rounded-xl text-xs font-extrabold transition-all duration-150 shrink-0 shadow-sm hover:scale-[1.02]"
        >
          <span>Start</span>
          <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
};

export default IssueCard;
