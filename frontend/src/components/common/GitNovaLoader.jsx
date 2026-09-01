import React from 'react';
import GitNovaLogo from '../GitNovaLogo';

/**
 * GitNovaLoader — Premium, centered cosmic logo loading animation.
 * Features a glowing, pulsing Nova star core with smooth orbital ring rotation.
 */
const GitNovaLoader = ({ 
  text = "Loading verified intelligence...", 
  subtext = "Aligning codebase evidence & repository AST",
  size = "md",
  fullScreen = false 
}) => {
  const sizeClasses = {
    sm: "w-12 h-12",
    md: "w-20 h-20",
    lg: "w-28 h-28"
  }[size] || "w-20 h-20";

  const content = (
    <div className="flex flex-col items-center justify-center p-8 text-center select-none">
      {/* Centered Glowing Logo Container */}
      <div className="relative flex items-center justify-center mb-6">
        {/* Breathing Outer Ambient Aura */}
        <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 via-teal-500/30 to-cyan-500/20 rounded-full blur-2xl animate-pulse" />
        
        {/* Pulsing Emerald Halo */}
        <div className="absolute inset-0 bg-emerald-400/20 rounded-full blur-lg animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite]" />

        {/* Animated GitNova Logo */}
        <div className="relative z-10 animate-[pulse_2s_ease-in-out_infinite]">
          <GitNovaLogo className={sizeClasses} static={false} />
        </div>
      </div>

      {/* Brand Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-3 shadow-[0_0_12px_rgba(16,185,129,0.15)]">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
        <span className="text-[11px] font-mono font-bold tracking-widest text-emerald-400 uppercase">
          GitNova
        </span>
      </div>

      {/* Main Status Text */}
      <p className="text-sm font-semibold text-slate-200 tracking-wide mb-1">
        {text}
      </p>

      {/* Secondary Tech Note */}
      {subtext && (
        <p className="text-xs text-slate-500 font-mono">
          {subtext}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#050B0E]/90 backdrop-blur-md">
        {content}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center w-full py-16">
      {content}
    </div>
  );
};

export default GitNovaLoader;
