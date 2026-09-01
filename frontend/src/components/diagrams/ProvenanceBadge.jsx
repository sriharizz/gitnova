import React from 'react';
import { ShieldCheck, UserCheck, Sparkles, Lightbulb } from 'lucide-react';

const PROVENANCE_CONFIGS = {
  VERIFIED_FACT: {
    label: 'Verified in Repo',
    bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: ShieldCheck,
    description: 'Directly verified from GitHub API, repository files, or CI configuration.'
  },
  MAINTAINER_INTENT: {
    label: 'Maintainer Guidance',
    bg: 'bg-blue-50 text-blue-700 border-blue-200',
    icon: UserCheck,
    description: 'Direct instruction or constraint posted by a repository maintainer.'
  },
  AI_INFERENCE: {
    label: 'AI Explanation',
    bg: 'bg-teal-50 text-teal-700 border-teal-200',
    icon: Sparkles,
    description: 'Grounded explanation synthesized from retrieved codebase context.'
  },
  IMPLEMENTATION_HYPOTHESIS: {
    label: 'Suggested Plan',
    bg: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: Lightbulb,
    description: 'Suggested implementation plan grounded in repository code.'
  }
};

export default function ProvenanceBadge({ type = 'VERIFIED_FACT', source = null, className = '' }) {
  const config = PROVENANCE_CONFIGS[type] || PROVENANCE_CONFIGS.VERIFIED_FACT;
  const Icon = config.icon;

  return (
    <div 
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.bg} ${className}`}
      title={`${config.label}: ${config.description}${source ? ` (Source: ${source})` : ''}`}
    >
      <Icon className="w-3.5 h-3.5" />
      <span>{config.label}</span>
      {source && (
        <span className="text-[10px] opacity-75 font-mono ml-0.5">· {source}</span>
      )}
    </div>
  );
}
