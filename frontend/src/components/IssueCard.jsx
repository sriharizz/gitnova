import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

const IssueCard = ({ issue, onSelect, isActive }) => {

    // --- COLOR THEME ENGINE ---
    const getTheme = (diff) => {
        switch (diff) {
            case 'Novice': return {
                // Green (Easy)
                badge: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
                border: isActive ? 'border-emerald-500 shadow-[0_0_30px_-5px_rgba(16,185,129,0.4)]' : 'border-slate-800 hover:border-emerald-500/50',
                icon: 'text-emerald-400',
            };
            case 'Apprentice': return {
                // Medium (Target) - Indigo
                badge: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
                border: isActive ? 'border-indigo-500 shadow-[0_0_30px_-5px_rgba(99,102,241,0.4)]' : 'border-slate-800 hover:border-indigo-500/50',
                icon: 'text-indigo-400',
            };
            case 'Contributor': return {
                // Rose (Hard)
                badge: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
                border: isActive ? 'border-rose-500 shadow-[0_0_30px_-5px_rgba(244,63,94,0.4)]' : 'border-slate-800 hover:border-rose-500/50',
                icon: 'text-rose-400',
            };
            default: return { badge: 'text-slate-400', border: 'border-slate-800', icon: 'text-slate-400' };
        }
    };

    const theme = getTheme(issue.difficulty);

    return (
        <div
            onClick={() => onSelect(issue)}
            className={`cursor-pointer group relative flex flex-col p-5 bg-[#1e293b] rounded-xl border transition-all duration-300 ${theme.border} ${isActive ? 'bg-[#162032] scale-[1.02]' : 'hover:-translate-y-1'}`}
        >
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                    <img src={issue.avatar_url} alt="repo" className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-700" />
                    <div className="min-w-0">
                        <h3 className={`text-xs font-bold font-mono ${theme.icon} truncate max-w-[120px]`}>{issue.repo_name}</h3>
                        <div className="text-[10px] text-slate-500 mt-0.5">{new Date(issue.created_at).toLocaleDateString()}</div>
                    </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${theme.badge}`}>
                    {issue.difficulty === 'Apprentice' ? 'Medium' : issue.difficulty}
                </span>
            </div>

            {/* Title */}
            <h2 className="text-sm font-bold text-slate-200 leading-snug line-clamp-2 mb-3 h-10">
                {issue.title}
            </h2>

            {/* Footer */}
            <div className="mt-auto flex items-center justify-between pt-3 border-t border-slate-700/50">
                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500">
                    <Sparkles className={`w-3 h-3 ${theme.icon}`} />
                    <span>AI Insight Ready</span>
                </div>
                <div className={`p-1.5 rounded-md bg-slate-800 text-slate-400 group-hover:text-white group-hover:bg-slate-700 transition-colors`}>
                    <ArrowRight className="w-4 h-4" />
                </div>
            </div>
        </div>
    );
};

export default IssueCard;