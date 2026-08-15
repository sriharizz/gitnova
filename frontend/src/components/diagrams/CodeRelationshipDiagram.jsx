import React from 'react';
import { FileCode, Hash, TestTube2, GitPullRequest, ArrowRight } from 'lucide-react';
import ProvenanceBadge from './ProvenanceBadge';

const NODE_CONFIG = {
  issue: {
    icon: GitPullRequest,
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    text: 'text-purple-900',
    tag: 'bg-purple-100 text-purple-700',
    typeLabel: 'GitHub Issue'
  },
  file: {
    icon: FileCode,
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    text: 'text-teal-900',
    tag: 'bg-teal-100 text-teal-700',
    typeLabel: 'Target File'
  },
  symbol: {
    icon: Hash,
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-900',
    tag: 'bg-blue-100 text-blue-700',
    typeLabel: 'Target Symbol'
  },
  test: {
    icon: TestTube2,
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-900',
    tag: 'bg-emerald-100 text-emerald-700',
    typeLabel: 'Test File'
  }
};

export default function CodeRelationshipDiagram({ diagram }) {
  if (!diagram || !diagram.nodes || diagram.nodes.length === 0) {
    return null;
  }

  const { title, description, nodes, edges } = diagram;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal-500" />
            {title || 'Code Relationship Map'}
          </h4>
          {description && (
            <p className="text-xs text-slate-500 mt-0.5">{description}</p>
          )}
        </div>
        <ProvenanceBadge type="VERIFIED_FACT" source="RRF AST Retrieval" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 py-2">
        {nodes.map((node) => {
          const config = NODE_CONFIG[node.node_type] || NODE_CONFIG.file;
          const Icon = config.icon;

          return (
            <div
              key={node.id}
              className={`p-3 rounded-lg border ${config.border} ${config.bg} flex flex-col justify-between space-y-2`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${config.tag}`}>
                  {config.typeLabel}
                </span>
                <Icon className="w-4 h-4 text-slate-600" />
              </div>
              <div>
                <p className={`text-xs font-mono font-medium ${config.text} break-all`}>
                  {node.label}
                </p>
              </div>
              {node.provenance && (
                <div className="pt-1 border-t border-slate-200/60">
                  <span className="text-[10px] text-slate-400 font-mono">
                    src: {node.provenance.source}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
