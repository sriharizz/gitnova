import React from 'react';
import { GitBranch, Code, Github, Users, Search, Terminal, Sparkles, GitPullRequest } from 'lucide-react';
import { useTheme } from '../../lib/ThemeContext';

/**
 * 3D Cosmic Orbital Field System (Without central planet ball)
 * Features:
 * - Concentric tilted elliptical rings with glowing green perspective lines
 * - Dynamically floating developer satellite nodes distributed across the cosmic field
 * - Glowing star dust particles and ambient nebula aura
 */
export const OrbitWidget = ({ className = '' }) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`relative flex items-center justify-center select-none pointer-events-none w-full ${className}`}>
      {/* Ambient Radial Nebula Glow */}
      <div 
        className={`absolute w-[500px] h-[220px] sm:w-[750px] sm:h-[260px] lg:w-[950px] lg:h-[300px] rounded-full blur-3xl -z-10 animate-pulse-glow transition-all duration-300 ${
          isDark 
            ? 'bg-gradient-to-r from-emerald-500/20 via-teal-400/25 to-emerald-600/20' 
            : 'bg-gradient-to-r from-teal-500/15 via-emerald-400/15 to-cyan-500/15'
        }`} 
      />

      {/* 3D Perspective Elliptical Orbital Stage */}
      <div className="relative w-[560px] h-[200px] sm:w-[800px] sm:h-[240px] lg:w-[1000px] lg:h-[270px] flex items-center justify-center">
        
        {/* Outer Orbit Ellipse */}
        <div 
          className={`absolute inset-0 rounded-[100%] border transition-colors duration-300 ${
            isDark 
              ? 'border-emerald-500/35 shadow-[0_0_40px_rgba(16,185,129,0.18)]' 
              : 'border-teal-500/30 shadow-[0_0_30px_rgba(20,184,166,0.15)]'
          }`}
          style={{ transform: 'scaleY(0.40)' }}
        />

        {/* Middle Orbit Ellipse (Dashed Tech Ring) */}
        <div 
          className={`absolute inset-x-12 inset-y-4 sm:inset-x-18 sm:inset-y-6 lg:inset-x-24 lg:inset-y-8 rounded-[100%] border border-dashed transition-colors duration-300 ${
            isDark ? 'border-emerald-400/40' : 'border-emerald-400/35'
          }`}
          style={{ transform: 'scaleY(0.40)' }}
        />

        {/* Inner Orbit Ellipse */}
        <div 
          className={`absolute inset-x-28 inset-y-8 sm:inset-x-40 sm:inset-y-10 lg:inset-x-52 lg:inset-y-14 rounded-[100%] border transition-colors duration-300 ${
            isDark ? 'border-emerald-400/30' : 'border-teal-400/25'
          }`}
          style={{ transform: 'scaleY(0.40)' }}
        />

        {/* Glowing Space Dust Particles */}
        <div className="absolute top-[26%] left-[16%] w-2 h-2 rounded-full bg-amber-400 blur-[0.5px] shadow-[0_0_8px_#F59E0B] animate-pulse" />
        <div className="absolute top-[20%] right-[14%] w-2 h-2 rounded-full bg-emerald-400 blur-[0.5px] shadow-[0_0_8px_#34D399] animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-[24%] left-[13%] w-2 h-2 rounded-full bg-teal-400 blur-[0.5px] shadow-[0_0_8px_#14B8A6] animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute bottom-[20%] right-[17%] w-2.5 h-2.5 rounded-full bg-emerald-300 blur-[0.5px] shadow-[0_0_8px_#6EE7B7] animate-pulse" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-[48%] left-[5%] w-1.5 h-1.5 rounded-full bg-emerald-300 blur-[0.5px] animate-pulse" style={{ animationDelay: '0.5s' }} />
        <div className="absolute top-[46%] right-[5%] w-1.5 h-1.5 rounded-full bg-teal-300 blur-[0.5px] animate-pulse" style={{ animationDelay: '2.5s' }} />
        <div className="absolute top-[32%] left-[48%] w-2 h-2 rounded-full bg-cyan-300 blur-[0.5px] shadow-[0_0_6px_#67E8F9] animate-pulse" style={{ animationDelay: '1.8s' }} />
        <div className="absolute bottom-[30%] right-[46%] w-2 h-2 rounded-full bg-emerald-400 blur-[0.5px] shadow-[0_0_6px_#34D399] animate-pulse" style={{ animationDelay: '0.8s' }} />

        {/* Floating Node 1: GitHub (Top Left) */}
        <div 
          className={`absolute top-[18%] left-[20%] sm:left-[22%] -translate-x-1/2 -translate-y-1/2 p-2.5 sm:p-3 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#08151D]/95 border border-slate-700/80 text-white shadow-[0_6px_20px_rgba(0,0,0,0.6)] hover:border-emerald-500/60' 
              : 'bg-white/95 border border-slate-200 text-slate-900 shadow-md hover:border-teal-400'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite' }}
          title="GitHub Integration"
        >
          <Github className="w-4 h-4 sm:w-4.5 sm:h-4.5" />
        </div>

        {/* Floating Node 2: GitBranch (Bottom Left) */}
        <div 
          className={`absolute bottom-[20%] left-[16%] sm:left-[18%] -translate-x-1/2 translate-y-1/2 p-2.5 sm:p-3 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#08151D]/95 border border-slate-700/80 text-white shadow-[0_6px_20px_rgba(0,0,0,0.6)] hover:border-emerald-500/60' 
              : 'bg-white/95 border border-slate-200 text-slate-800 shadow-md hover:border-teal-400'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite', animationDelay: '3s' }}
          title="Git Branching & PRs"
        >
          <GitBranch className="w-4 h-4 sm:w-4.5 sm:h-4.5" />
        </div>

        {/* Floating Node 3: Code </> (Top Right) */}
        <div 
          className={`absolute top-[18%] right-[20%] sm:right-[22%] translate-x-1/2 -translate-y-1/2 p-2.5 sm:p-3 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#08151D]/95 border border-slate-700/80 text-[#34D399] shadow-[0_6px_20px_rgba(0,0,0,0.6)] hover:border-emerald-500/60' 
              : 'bg-white/95 border border-slate-200 text-teal-700 shadow-md hover:border-teal-400'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite', animationDelay: '1.8s' }}
          title="AST Code Intelligence"
        >
          <Code className="w-4 h-4 sm:w-4.5 sm:h-4.5 font-bold" />
        </div>

        {/* Floating Node 4: Community Users (Bottom Right) */}
        <div 
          className={`absolute bottom-[20%] right-[16%] sm:right-[18%] translate-x-1/2 translate-y-1/2 p-2.5 sm:p-3 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#08151D]/95 border border-slate-700/80 text-white shadow-[0_6px_20px_rgba(0,0,0,0.6)] hover:border-emerald-500/60' 
              : 'bg-white/95 border border-slate-200 text-teal-700 shadow-md hover:border-teal-400'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite', animationDelay: '4.5s' }}
          title="Active Maintainers & Community"
        >
          <Users className="w-4 h-4 sm:w-4.5 sm:h-4.5" />
        </div>

        {/* Floating Node 5: Smart Search (Center Left on inner ring) */}
        <div 
          className={`absolute top-[44%] left-[32%] sm:left-[35%] -translate-x-1/2 -translate-y-1/2 p-2 sm:p-2.5 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#091822]/90 border border-slate-700/70 text-slate-300 shadow-[0_4px_15px_rgba(0,0,0,0.5)] hover:border-emerald-500/60' 
              : 'bg-white/90 border border-slate-200 text-slate-700 shadow-sm hover:border-teal-400'
          }`}
          style={{ animation: 'float 5s ease-in-out infinite', animationDelay: '2.4s' }}
          title="Issue Filtering"
        >
          <Search className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#34D399]" />
        </div>

        {/* Floating Node 6: Terminal (Center Right on inner ring) */}
        <div 
          className={`absolute top-[44%] right-[32%] sm:right-[35%] translate-x-1/2 -translate-y-1/2 p-2 sm:p-2.5 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#091822]/90 border border-slate-700/70 text-slate-300 shadow-[0_4px_15px_rgba(0,0,0,0.5)] hover:border-emerald-500/60' 
              : 'bg-white/90 border border-slate-200 text-slate-700 shadow-sm hover:border-teal-400'
          }`}
          style={{ animation: 'float 5s ease-in-out infinite', animationDelay: '3.8s' }}
          title="Automated Test Execution"
        >
          <Terminal className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-teal-400" />
        </div>

        {/* Floating Node 7: AI Sparkles (Center Top on middle ring) */}
        <div 
          className={`absolute top-[8%] left-[50%] -translate-x-1/2 -translate-y-1/2 p-2 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#0A1B24]/90 border border-emerald-500/40 text-amber-300 shadow-[0_0_15px_rgba(52,211,153,0.3)]' 
              : 'bg-white border border-teal-200 text-amber-500 shadow-sm'
          }`}
          style={{ animation: 'float 5.5s ease-in-out infinite', animationDelay: '1.2s' }}
          title="Grounded Intelligence"
        >
          <Sparkles className="w-3.5 h-3.5" />
        </div>

        {/* Floating Node 8: Pull Request (Center Bottom on middle ring) */}
        <div 
          className={`absolute bottom-[8%] left-[50%] -translate-x-1/2 translate-y-1/2 p-2 rounded-full transition-all pointer-events-auto hover:scale-115 cursor-pointer z-20 ${
            isDark 
              ? 'bg-[#0A1B24]/90 border border-emerald-500/40 text-[#34D399] shadow-[0_0_15px_rgba(52,211,153,0.3)]' 
              : 'bg-white border border-teal-200 text-teal-600 shadow-sm'
          }`}
          style={{ animation: 'float 5.5s ease-in-out infinite', animationDelay: '4s' }}
          title="Pull Request Delivery"
        >
          <GitPullRequest className="w-3.5 h-3.5" />
        </div>

      </div>
    </div>
  );
};

export default OrbitWidget;
