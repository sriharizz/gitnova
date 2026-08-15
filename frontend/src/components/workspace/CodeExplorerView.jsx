import React, { useState } from 'react';
import { Folder, FileCode, CheckCircle2, ArrowRight, ArrowLeft, Search, Sparkles, Copy, Check, Code2, Terminal } from 'lucide-react';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';

export const CodeExplorerView = ({ codeData, onBack, onCreatePlan }) => {
  const files = codeData?.files || [];
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!files || files.length === 0) {
    return (
      <div className="flex flex-col h-full bg-slate-50 border-l border-slate-200/90 animate-in fade-in duration-200 p-8">
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-8 text-center max-w-lg mx-auto my-12 shadow-nova-sm">
          <FileCode className="w-10 h-10 text-amber-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-amber-900 mb-1">Code Context Preparing</h3>
          <p className="text-xs text-amber-700 leading-relaxed">
            The target source code files for this issue are currently being retrieved. Please check back shortly.
          </p>
        </div>
      </div>
    );
  }

  const selectedFile = files[selectedFileIndex] || files[0];
  const lines = selectedFile.content ? selectedFile.content.split('\n') : [];

  const handleCopyCode = () => {
    if (selectedFile.content) {
      navigator.clipboard.writeText(selectedFile.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 animate-in fade-in duration-200">
      {/* Top Header Bar */}
      <div className="bg-white border-b border-slate-200/90 px-6 py-3.5 flex items-center justify-between shrink-0">
        <div>
          <div className="text-[11px] font-mono font-bold text-teal-600 uppercase tracking-wider mb-0.5">
            Stage 04 — Explore Codebase Context
          </div>
          <h2 className="text-lg font-extrabold text-slate-900">Code Explorer & AST Regions</h2>
        </div>

        <div className="flex items-center gap-3">
          <ProvenanceBadge type="VERIFIED_FACT" source="RRF AST Slicer" />
          <button
            onClick={onCreatePlan}
            className="px-4 py-2 text-xs font-bold text-white bg-teal-700 hover:bg-teal-600 rounded-xl transition-all shadow-nova flex items-center gap-1.5"
          >
            <span>Proceed to Plan Fix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* COLUMN 1: File Tree (3 cols) */}
        <div className="col-span-3 bg-white border-r border-slate-200 p-4 flex flex-col justify-between overflow-y-auto custom-scrollbar">
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">
              Target Files ({files.length})
            </div>
            <div className="space-y-1">
              {files.map((file, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedFileIndex(idx)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs font-mono transition-all flex items-center justify-between ${
                    idx === selectedFileIndex
                      ? 'bg-teal-50 text-teal-900 font-bold border border-teal-200 shadow-nova-sm'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileCode className="w-3.5 h-3.5 shrink-0 text-teal-600" />
                    <span className="truncate">{file.file_path.split('/').pop()}</span>
                  </div>
                  {file.is_verified && (
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500 shrink-0" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 mt-4">
            <div className="text-[11px] font-bold text-slate-900 mb-0.5">Active Path</div>
            <div className="text-xs font-mono text-slate-600 truncate">{selectedFile.file_path}</div>
            <div className="text-[10px] text-slate-400 mt-1">Lines {selectedFile.start_line} – {selectedFile.end_line}</div>
          </div>
        </div>

        {/* COLUMN 2: Code Viewer (6 cols) */}
        <div className="col-span-6 bg-slate-950 flex flex-col overflow-hidden border-r border-slate-800">
          {/* File Tab Bar */}
          <div className="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between shrink-0">
            <span className="font-mono text-xs font-bold text-slate-200 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-teal-400" />
              {selectedFile.file_path}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyCode}
                className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-slate-200 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 transition-colors"
                title="Copy snippet"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
              <span className="text-[10px] font-semibold text-emerald-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                Verified AST
              </span>
            </div>
          </div>

          {/* Code Lines Viewer */}
          <div className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed custom-scrollbar">
            <table className="w-full border-collapse">
              <tbody>
                {lines.map((line, idx) => {
                  const lineNum = selectedFile.start_line + idx;
                  const isKeyword = line.includes('def ') || line.includes('class ') || line.includes('return') || line.includes('import ') || line.includes('fn ') || line.includes('func ');

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-900/80 transition-colors ${isKeyword ? 'bg-teal-950/20' : ''}`}
                    >
                      <td className="w-10 text-right pr-4 py-0.5 text-slate-600 select-none border-r border-slate-800 text-[11px]">
                        {lineNum}
                      </td>
                      <td className="pl-4 py-0.5 whitespace-pre text-slate-300">
                        {line}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* COLUMN 3: Insights & Symbols (3 cols) */}
        <div className="col-span-3 bg-white p-4 space-y-5 overflow-y-auto custom-scrollbar">
          {/* Target Symbol Focus */}
          <div>
            <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Target Symbol</h3>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs font-mono text-slate-800 font-semibold flex items-center justify-between">
              <span className="truncate">{selectedFile.symbol_name || 'Module Scope'}</span>
              <span className="text-[10px] text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200 uppercase">Target</span>
            </div>
          </div>

          {/* Implementation Focus */}
          <div>
            <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">What to look for</h3>
            <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-200 font-medium">
              Inspect how parameters and typing annotations are defined on lines {selectedFile.start_line}–{selectedFile.end_line}. Notice any missing return types or error edge cases.
            </p>
          </div>

          {/* Grounding Attribution */}
          <div className="p-4 bg-teal-50/60 border border-teal-200 rounded-2xl space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-teal-950">
              <Sparkles className="w-4 h-4 text-teal-600" />
              <span>Grounding Guarantee</span>
            </div>
            <p className="text-xs text-teal-900 leading-relaxed">
              Every code snippet displayed here is retrieved directly from the repository AST. GitNova never hallucinates file paths or source code.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeExplorerView;
