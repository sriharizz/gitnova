import React from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle2, Clock, User, ExternalLink, HelpCircle } from 'lucide-react';

export const ContributionStatusView = ({ issue, onNextStage }) => {
  if (!issue) return null;

  const {
    repo_full_name,
    github_issue_number,
    title,
    reporter_username = 'community_contributor',
    availability_status = 'LIKELY_AVAILABLE',
    opportunity_confidence = 'HIGH',
    opportunity_signals = {},
    opportunity_evidence = [],
    opportunity_warnings = [],
    last_verified_at,
    github_url
  } = issue;

  const evidenceList = opportunity_evidence.length > 0 ? opportunity_evidence : (
    opportunity_signals?.evidence_statements || [
      "✓ Open on GitHub",
      "✓ Unassigned on GitHub",
      "✓ Verified target location"
    ]
  );

  const warningsList = opportunity_warnings.length > 0 ? opportunity_warnings : (
    opportunity_signals?.warnings || []
  );

  const statusColorClass = (
    availability_status === 'LIKELY_AVAILABLE'
      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
      : availability_status === 'CHECK_DISCUSSION'
      ? 'bg-amber-50 text-amber-800 border-amber-200'
      : 'bg-gray-100 text-gray-700 border-gray-200'
  );

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-6 animate-in fade-in duration-200">
      {/* Stage Header */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-4">
        <div>
          <div className="text-xs font-mono font-bold text-emerald-600 uppercase tracking-wider">
            Stage 2 — Check Status
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight mt-1">
            Contribution Opportunity Status & Evidence
          </h1>
        </div>
        <a
          href={github_url || `https://github.com/${repo_full_name}/issues/${github_issue_number}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-white rounded-xl text-xs font-semibold transition-all shadow-nova-sm"
        >
          <span>View on GitHub</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* Primary Status Banner */}
      <div className={`p-6 rounded-2xl border ${statusColorClass} shadow-nova-sm`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            {availability_status === 'LIKELY_AVAILABLE' ? (
              <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
            ) : availability_status === 'CHECK_DISCUSSION' ? (
              <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
            ) : (
              <ShieldCheck className="w-6 h-6 text-gray-500 shrink-0 mt-0.5" />
            )}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-extrabold text-base tracking-wide uppercase">
                  {availability_status.replace('_', ' ')}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-md font-semibold bg-white/70 border border-current/20">
                  Confidence: {opportunity_confidence}
                </span>
              </div>
              <p className="text-xs opacity-90 leading-relaxed max-w-xl">
                {availability_status === 'LIKELY_AVAILABLE'
                  ? "Based on the latest GitHub activity sync, this issue appears open, unassigned, and available for contribution."
                  : availability_status === 'CHECK_DISCUSSION'
                  ? "This issue has soft triage labels or active discussion on GitHub. Check the GitHub discussion before starting work."
                  : "This issue is closed, assigned, or marked with a hard rejection label on GitHub."}
              </p>
            </div>
          </div>

          <div className="shrink-0 flex flex-col items-end text-xs opacity-80 font-mono">
            <span className="flex items-center gap-1">
              <User className="w-3.5 h-3.5" /> Reported by @{reporter_username}
            </span>
            {last_verified_at && (
              <span className="flex items-center gap-1 mt-1">
                <Clock className="w-3.5 h-3.5" /> Verified {new Date(last_verified_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Grounded Evidence List */}
      <div className="bg-white border border-gray-200/90 rounded-2xl p-6 shadow-nova-sm">
        <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" /> Grounded GitHub Evidence
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {evidenceList.map((stmt, idx) => (
            <div key={idx} className="flex items-center gap-2.5 p-3 rounded-xl bg-gray-50 border border-gray-100 text-xs font-semibold text-gray-800">
              <span className="text-emerald-600 font-bold">{stmt.startsWith('✓') ? '✓' : '•'}</span>
              <span>{stmt.replace('✓ ', '')}</span>
            </div>
          ))}
        </div>

        {warningsList.length > 0 && (
          <div className="mt-4 p-4 bg-amber-50/80 border border-amber-200 rounded-xl space-y-2">
            <h3 className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-600" /> Pre-Flight Warnings
            </h3>
            <ul className="space-y-1">
              {warningsList.map((warn, idx) => (
                <li key={idx} className="text-xs text-amber-800 font-medium">
                  {warn}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Disclaimers & Advice */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-3">
        <HelpCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <p className="text-xs text-slate-600 leading-relaxed">
          <strong>Open-Source Policy Reminder:</strong> GitNova provides signals based on GitHub API checks. Always leave a polite comment on the original GitHub issue stating your intent to work on it before submitting code.
        </p>
      </div>

      {/* Action Footer */}
      {onNextStage && (
        <div className="flex justify-end pt-4">
          <button
            onClick={onNextStage}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition-all shadow-nova-sm"
          >
            Next Stage: Learn Concepts →
          </button>
        </div>
      )}
    </div>
  );
};

export default ContributionStatusView;
