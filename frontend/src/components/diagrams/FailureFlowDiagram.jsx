import React, { useState } from 'react';
import { AlertTriangle, PlayCircle, Zap, ShieldAlert, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react';
import ProvenanceBadge from './ProvenanceBadge';
import { useTheme } from '../../lib/ThemeContext';

const NODE_STYLES = {
  trigger: {
    icon: PlayCircle,
    borderDark: 'border-blue-500/40 bg-blue-950/30 text-blue-200',
    borderLight: 'border-blue-200 bg-blue-50/70 text-blue-900',
    badgeDark: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    badgeLight: 'bg-blue-100 text-blue-800 border-blue-200',
    iconColor: 'text-blue-400',
    label: '01 · TRIGGER'
  },
  current: {
    icon: Zap,
    borderDark: 'border-slate-700 bg-[#09151E] text-slate-200',
    borderLight: 'border-slate-200 bg-slate-50 text-slate-800',
    badgeDark: 'bg-slate-800 text-slate-300 border-slate-700',
    badgeLight: 'bg-slate-200/80 text-slate-700 border-slate-300',
    iconColor: 'text-teal-400',
    label: '02 · EXECUTION'
  },
  failure: {
    icon: AlertTriangle,
    borderDark: 'border-rose-500/50 bg-rose-950/30 text-rose-200',
    borderLight: 'border-rose-200 bg-rose-50/70 text-rose-900',
    badgeDark: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    badgeLight: 'bg-rose-100 text-rose-800 border-rose-200',
    iconColor: 'text-rose-400 animate-pulse',
    label: '03 · ROOT DEFECT'
  },
  consequence: {
    icon: ShieldAlert,
    borderDark: 'border-amber-500/40 bg-amber-950/30 text-amber-200',
    borderLight: 'border-amber-200 bg-amber-50/70 text-amber-900',
    badgeDark: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    badgeLight: 'bg-amber-100 text-amber-800 border-amber-200',
    iconColor: 'text-amber-400',
    label: '04 · CONSEQUENCE'
  }
};

export default function FailureFlowDiagram({ diagram }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [expandedNodes, setExpandedNodes] = useState({});

  if (!diagram || !diagram.nodes || diagram.nodes.length === 0) {
    return (
      <div className={`p-4 rounded-2xl border text-xs font-mono ${
        isDark ? 'border-slate-800 bg-[#050B0E] text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-500'
      }`}>
        Evidence in progress for control flow graph.
      </div>
    );
  }

  const { title, description, nodes } = diagram;

  const toggleExpand = (nodeId) => {
    setExpandedNodes(prev => ({ ...prev, [nodeId]: !prev[nodeId] }));
  };

  return (
    <div className={`rounded-2xl border p-5 space-y-4 transition-colors ${
      isDark 
        ? 'bg-[#060F15] border-slate-800/90 text-white shadow-md' 
        : 'bg-white border-slate-200/90 text-slate-900 shadow-nova-sm'
    }`}>
      {/* Header */}
      <div className={`flex items-center justify-between border-b pb-3.5 ${
        isDark ? 'border-slate-800/80' : 'border-slate-100'
      }`}>
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
          <div>
            <h4 className={`text-xs font-bold uppercase tracking-wider ${
              isDark ? 'text-slate-200' : 'text-slate-900'
            }`}>
              {title || 'Control Flow & Failure Trace'}
            </h4>
            {description && (
              <p className={`text-[11px] mt-0.5 ${
                isDark ? 'text-slate-400' : 'text-slate-500'
              }`}>{description}</p>
            )}
          </div>
        </div>
        <ProvenanceBadge type="VERIFIED_FACT" source="AST Call Graph & Grounding" />
      </div>

      {/* Sequential Flow Nodes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-stretch py-1">
        {nodes.map((node, index) => {
          const style = NODE_STYLES[node.node_type] || NODE_STYLES.current;
          const Icon = style.icon;
          const detail = node.metadata?.detail;
          const isNodeExpanded = expandedNodes[node.id || index];
          const isLongDetail = detail && detail.length > 130;

          return (
            <div
              key={node.id || index}
              className={`p-4 rounded-xl border flex flex-col justify-between transition-all duration-150 ${
                isDark ? style.borderDark : style.borderLight
              }`}
            >
              {/* Top: Badge + Icon */}
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                  isDark ? style.badgeDark : style.badgeLight
                }`}>
                  {style.label}
                </span>
                <Icon className={`w-4 h-4 ${style.iconColor} shrink-0`} />
              </div>

              {/* Middle: Content Aligned to Top */}
              <div className="flex-1 space-y-1.5 mb-4">
                <p className={`text-xs font-bold leading-snug ${
                  isDark ? 'text-white' : 'text-slate-900'
                }`}>
                  {node.label}
                </p>
                
                {detail && (
                  <div>
                    <p className={`text-[11px] leading-relaxed font-mono ${
                      isNodeExpanded ? '' : (isLongDetail ? 'line-clamp-4' : '')
                    } ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                      {detail}
                    </p>

                    {isLongDetail && (
                      <button
                        onClick={() => toggleExpand(node.id || index)}
                        className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-[#34D399] hover:underline mt-1 font-sans"
                      >
                        <span>{isNodeExpanded ? 'Show less' : 'Read more'}</span>
                        {isNodeExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Bottom: Pinned Step Footer */}
              <div className={`mt-auto pt-2.5 border-t flex items-center justify-between text-[10px] font-mono ${
                isDark ? 'border-white/10 text-slate-400' : 'border-slate-200 text-slate-500'
              }`}>
                <span>Step {index + 1}</span>
                {index < nodes.length - 1 && (
                  <ChevronRight className={`w-3.5 h-3.5 ${isDark ? 'text-slate-600' : 'text-slate-400'}`} />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
