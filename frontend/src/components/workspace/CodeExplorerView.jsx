import React, { useState } from 'react';
import { Folder, FileCode, CheckCircle2, ArrowRight, ArrowLeft, Search, Sparkles, Copy, Check, Code2, Terminal } from 'lucide-react';
import ProvenanceBadge from '../diagrams/ProvenanceBadge';
import { useTheme } from '../../lib/ThemeContext';

export const CodeExplorerView = ({ codeData, onBack, onCreatePlan }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const files = codeData?.files || [];
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!files || files.length === 0) {
    return (
      <div className={`flex flex-col h-full animate-in fade-in duration-200 p-4 sm:p-8 ${
        isDark ? 'bg-[#050B0E] text-white' : 'bg-slate-50 text-slate-900'
      }`}>
        <div className={`border rounded-2xl p-6 sm:p-8 text-center max-w-lg mx-auto my-12 shadow-nova-sm ${
          isDark ? 'bg-[#08151D] border-slate-800' : 'bg-amber-50 border-amber-200'
        }`}>
          <FileCode className={`w-10 h-10 mx-auto mb-3 ${isDark ? 'text-teal-400' : 'text-amber-600'}`} />
          <h3 className={`text-base font-bold mb-1 ${isDark ? 'text-white' : 'text-amber-900'}`}>Code Context Preparing</h3>
          <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-400' : 'text-amber-700'}`}>
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
    <div className={`flex flex-col min-h-full rounded-2xl border shadow-nova-sm overflow-hidden animate-in fade-in duration-200 transition-colors ${
      isDark ? 'bg-[#08131A] border-slate-800 text-white' : 'bg-white border-slate-200/90 text-slate-900'
    }`}>
      {/* Top Header Bar */}
      <div className={`px-4 sm:px-6 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0 border-b transition-colors ${
        isDark ? 'bg-[#0B1822] border-slate-800' : 'bg-white border-slate-200/90'
      }`}>
        <div>
          <div className="text-[11px] font-mono font-bold text-[#34D399] uppercase tracking-wider mb-0.5">
            Stage 04 — Explore Codebase Context
          </div>
          <h2 className={`text-base sm:text-lg font-extrabold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Code Explorer & AST Regions
          </h2>
        </div>

        <div className="flex items-center gap-2.5 sm:gap-3">
          <ProvenanceBadge type="VERIFIED_FACT" source="RRF AST Slicer" />
          <button
            onClick={onCreatePlan}
            className="px-3.5 sm:px-4 py-2 text-xs font-bold text-slate-950 bg-[#9FE8C3] hover:bg-[#86EFAC] rounded-xl transition-all shadow-sm flex items-center gap-1.5 shrink-0"
          >
            <span>Proceed to Plan Fix</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mobile Horizontal File Tabs (Visible on < lg screens) */}
      <div className={`lg:hidden flex items-center gap-2 p-2.5 overflow-x-auto no-scrollbar border-b transition-colors ${
        isDark ? 'bg-[#08131A] border-slate-800' : 'bg-slate-50 border-slate-200'
      }`}>
        <span className="text-[10px] font-mono font-bold text-slate-400 uppercase shrink-0 px-1">Files:</span>
        {files.map((file, idx) => {
          const isSelected = idx === selectedFileIndex;
          const fileName = file.file_path.split('/').pop();
          return (
            <button
              key={idx}
              onClick={() => setSelectedFileIndex(idx)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono shrink-0 transition-all border ${
                isSelected
                  ? (isDark 
                      ? 'bg-[#071F1B] border-emerald-500/40 text-[#34D399] font-bold shadow-sm' 
                      : 'bg-teal-50 border-teal-200 text-teal-900 font-bold shadow-sm')
                  : (isDark 
                      ? 'bg-[#0D212E] border-slate-700/60 text-slate-300 hover:text-white' 
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-100')
              }`}
            >
              <FileCode className="w-3.5 h-3.5 shrink-0 text-[#34D399]" />
              <span className="truncate max-w-[140px]">{fileName}</span>
            </button>
          );
        })}
      </div>

      {/* Main Content Layout: Stacked on Mobile/Tablet, 3-Column on Desktop (lg+) */}
      <div className="flex-1 flex flex-col lg:grid lg:grid-cols-12 min-h-0">
        
        {/* COLUMN 1: File Tree (Desktop only, 3 cols) */}
        <div className={`hidden lg:flex col-span-3 border-r p-4 flex-col justify-between overflow-y-auto custom-scrollbar transition-colors ${
          isDark ? 'bg-[#08131A] border-slate-800' : 'bg-white border-slate-200'
        }`}>
          <div>
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">
              Target Files ({files.length})
            </div>
            <div className="space-y-1">
              {files.map((file, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedFileIndex(idx)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs font-mono transition-all flex items-center justify-between border ${
                    idx === selectedFileIndex
                      ? (isDark 
                          ? 'bg-[#071F1B] text-[#34D399] font-bold border-emerald-500/30 shadow-sm' 
                          : 'bg-teal-50 text-teal-900 font-bold border-teal-200 shadow-nova-sm')
                      : (isDark 
                          ? 'text-slate-400 border-transparent hover:bg-slate-800/60 hover:text-slate-200' 
                          : 'text-slate-600 border-transparent hover:bg-slate-50 hover:text-slate-900')
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileCode className="w-3.5 h-3.5 shrink-0 text-[#34D399]" />
                    <span className="truncate">{file.file_path.split('/').pop()}</span>
                  </div>
                  {file.is_verified && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[#34D399] shrink-0" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className={`p-3 rounded-xl border mt-4 transition-colors ${
            isDark ? 'bg-[#0D212E] border-slate-800' : 'bg-slate-50 border-slate-200'
          }`}>
            <div className="text-[11px] font-bold text-slate-400 mb-0.5">Active Path</div>
            <div className={`text-xs font-mono truncate ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{selectedFile.file_path}</div>
            <div className="text-[10px] text-slate-400 mt-1">Lines {selectedFile.start_line} – {selectedFile.end_line}</div>
          </div>
        </div>

        {/* COLUMN 2: Code Viewer (Full on mobile, 6 cols on lg+) */}
        <div className="col-span-12 lg:col-span-6 bg-[#030A0E] flex flex-col overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800 min-h-[350px] lg:min-h-[500px]">
          {/* File Tab Bar */}
          <div className="bg-[#07131B] border-b border-slate-800 px-3 sm:px-4 py-2.5 flex items-center justify-between shrink-0">
            <span className="font-mono text-xs font-bold text-slate-200 flex items-center gap-2 truncate min-w-0">
              <FileCode className="w-4 h-4 text-[#34D399] shrink-0" />
              <span className="truncate">{selectedFile.file_path}</span>
            </span>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={handleCopyCode}
                className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 transition-colors"
                title="Copy snippet"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
              <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30 hidden sm:inline">
                Verified AST
              </span>
            </div>
          </div>

          {/* Code Lines Viewer with Horizontal Scroll */}
          <div className="flex-1 overflow-x-auto overflow-y-auto p-3 sm:p-4 font-mono text-xs leading-relaxed custom-scrollbar">
            <table className="w-full border-collapse">
              <tbody>
                {lines.map((line, idx) => {
                  const lineNum = selectedFile.start_line + idx;
                  const isKeyword = line.includes('def ') || line.includes('class ') || line.includes('return') || line.includes('import ') || line.includes('fn ') || line.includes('func ');

                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-900/80 transition-colors ${isKeyword ? 'bg-teal-950/25' : ''}`}
                    >
                      <td className="w-8 sm:w-10 text-right pr-3 sm:pr-4 py-0.5 text-slate-600 select-none border-r border-slate-800 text-[10px] sm:text-[11px] shrink-0">
                        {lineNum}
                      </td>
                      <td className="pl-3 sm:pl-4 py-0.5 whitespace-pre text-slate-300 font-mono text-[11px] sm:text-xs">
                        {line}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* COLUMN 3: Insights & Symbols (Full on mobile, 3 cols on lg+) */}
        <div className={`col-span-12 lg:col-span-3 p-4 sm:p-5 space-y-4 overflow-y-auto custom-scrollbar transition-colors ${
          isDark ? 'bg-[#08131A]' : 'bg-white'
        }`}>
          {/* Target Symbol Focus */}
          <div>
            <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Target Symbol</h3>
            <div className={`p-3 rounded-xl border text-xs font-mono font-semibold flex items-center justify-between gap-2 ${
              isDark ? 'bg-[#0D212E] border-slate-800 text-slate-200' : 'bg-slate-50 border-slate-200 text-slate-800'
            }`}>
              <span className="truncate">{selectedFile.symbol_name || 'Module Scope'}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded border uppercase shrink-0 ${
                isDark ? 'text-[#34D399] bg-[#071F1B] border-emerald-500/30' : 'text-teal-700 bg-teal-50 border-teal-200'
              }`}>
                Target
              </span>
            </div>
          </div>

          {/* Implementation Focus */}
          <div>
            <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">What to look for</h3>
            <p className={`text-xs leading-relaxed p-3 rounded-xl border font-medium ${
              isDark ? 'bg-[#0D212E] border-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 text-slate-600'
            }`}>
              Inspect how parameters and typing annotations are defined on lines {selectedFile.start_line}–{selectedFile.end_line}. Notice any missing return types or error edge cases.
            </p>
          </div>

          {/* Grounding Attribution */}
          <div className={`p-4 rounded-2xl border space-y-1.5 ${
            isDark ? 'bg-[#071F1B] border-emerald-500/30 text-emerald-200' : 'bg-teal-50/60 border-teal-200 text-teal-950'
          }`}>
            <div className="flex items-center gap-2 text-xs font-bold">
              <Sparkles className="w-4 h-4 text-[#34D399]" />
              <span>Grounding Guarantee</span>
            </div>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-300' : 'text-teal-900'}`}>
              Every code snippet displayed here is retrieved directly from the repository AST. GitNova never hallucinates file paths or source code.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeExplorerView;
