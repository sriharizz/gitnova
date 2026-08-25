import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Search, BookOpen, Rocket, Sun, Moon, Github, Code, GitBranch, Users, Sparkles, Terminal } from 'lucide-react';
import GitNovaLogo from '../components/GitNovaLogo';
import { useTheme } from '../lib/ThemeContext';

export const LandingPage = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen md:h-screen w-full overflow-y-auto md:overflow-hidden font-sans flex flex-col justify-between select-none p-4 sm:p-7 lg:px-12 lg:py-6 transition-colors duration-300 relative ${
      isDark ? 'bg-[#050B0E] text-white' : 'bg-[#F8FAFC] text-slate-900'
    }`}>
      
      {/* Ambient Cosmic Background Lighting */}
      <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[250px] sm:w-[900px] sm:h-[500px] rounded-full blur-[100px] sm:blur-[130px] -z-10 pointer-events-none transition-all duration-500 ${
        isDark 
          ? 'bg-gradient-to-r from-emerald-500/15 via-teal-400/20 to-emerald-600/15' 
          : 'bg-gradient-to-r from-teal-500/10 via-emerald-400/10 to-cyan-500/10'
      }`} />

      {/* Floating Developer Nodes (Subtle, Clean, Organic Placement on Desktop only) */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-0 hidden md:block">
        {/* GitHub Node (Top Left) */}
        <div 
          className={`absolute top-[22%] left-[12%] sm:left-[15%] p-3 rounded-2xl transition-all shadow-lg ${
            isDark 
              ? 'bg-[#08151D]/90 border border-slate-700/70 text-white shadow-[0_6px_20px_rgba(0,0,0,0.5)]' 
              : 'bg-white border border-slate-200 text-slate-800 shadow-md'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite' }}
        >
          <Github className="w-5 h-5" />
        </div>

        {/* Code Node (Top Right) */}
        <div 
          className={`absolute top-[24%] right-[12%] sm:right-[15%] p-3 rounded-2xl transition-all shadow-lg ${
            isDark 
              ? 'bg-[#08151D]/90 border border-slate-700/70 text-[#34D399] shadow-[0_6px_20px_rgba(0,0,0,0.5)]' 
              : 'bg-white border border-slate-200 text-teal-600 shadow-md'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite', animationDelay: '1.5s' }}
        >
          <Code className="w-5 h-5 font-bold" />
        </div>

        {/* Git Branch Node (Bottom Left) */}
        <div 
          className={`absolute bottom-[28%] left-[10%] sm:left-[14%] p-3 rounded-2xl transition-all shadow-lg ${
            isDark 
              ? 'bg-[#08151D]/90 border border-slate-700/70 text-slate-300 shadow-[0_6px_20px_rgba(0,0,0,0.5)]' 
              : 'bg-white border border-slate-200 text-slate-700 shadow-md'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite', animationDelay: '3s' }}
        >
          <GitBranch className="w-5 h-5" />
        </div>

        {/* Community Users Node (Bottom Right) */}
        <div 
          className={`absolute bottom-[28%] right-[10%] sm:right-[14%] p-3 rounded-2xl transition-all shadow-lg ${
            isDark 
              ? 'bg-[#08151D]/90 border border-slate-700/70 text-slate-300 shadow-[0_6px_20px_rgba(0,0,0,0.5)]' 
              : 'bg-white border border-slate-200 text-slate-700 shadow-md'
          }`}
          style={{ animation: 'float 6s ease-in-out infinite', animationDelay: '4.5s' }}
        >
          <Users className="w-5 h-5" />
        </div>

        {/* Small AI Sparkle Particle (Top Center-Right) */}
        <div 
          className="absolute top-[18%] right-[32%] p-2 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
          style={{ animation: 'float 5s ease-in-out infinite', animationDelay: '2s' }}
        >
          <Sparkles className="w-3.5 h-3.5" />
        </div>

        {/* Small Terminal Particle (Bottom Center-Left) */}
        <div 
          className="absolute bottom-[25%] left-[30%] p-2 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400"
          style={{ animation: 'float 5s ease-in-out infinite', animationDelay: '3.8s' }}
        >
          <Terminal className="w-3.5 h-3.5" />
        </div>
      </div>

      {/* 1. Top Navbar */}
      <header className="w-full max-w-7xl mx-auto flex items-center justify-between z-30 shrink-0">
        {/* Brand Logo with 4-Point Star and Orbital Rings */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <GitNovaLogo className="w-7 h-7 sm:w-8 sm:h-8" static={true} />
          <span className={`font-extrabold text-xl sm:text-2xl tracking-tight transition-colors ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            GitNova
          </span>
        </Link>

        {/* Center Navigation Links (Desktop) */}
        <nav className={`hidden md:flex items-center gap-9 text-sm font-medium transition-colors ${
          isDark ? 'text-slate-300' : 'text-slate-600'
        }`}>
          <a href="#how-it-works" className="hover:text-[#34D399] transition-colors">How it works</a>
          <Link to="/onboarding" className="hover:text-[#34D399] transition-colors">Learn</Link>
          <a href="#about" className="hover:text-[#34D399] transition-colors">About</a>
          <Link to="/issues" className="hover:text-[#34D399] transition-colors">Pricing</Link>
        </nav>

        {/* Right Action: Theme Switcher & Get Started */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-xl border transition-all duration-200 ${
              isDark 
                ? 'bg-[#09151D] border-slate-700/80 text-amber-300 hover:border-emerald-500/50 hover:bg-[#0E202B]' 
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
            title={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Get Started Button */}
          <Link
            to="/onboarding"
            className="px-4 py-2 sm:px-6 sm:py-2.5 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#064E3B] font-bold text-xs sm:text-sm rounded-2xl transition-all shadow-[0_0_15px_rgba(159,232,195,0.3)] hover:scale-[1.02]"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* 2. Hero Section (Centered Vertically and Horizontally) */}
      <main className="relative flex-1 flex flex-col items-center justify-center w-full max-w-4xl mx-auto z-10 text-center px-2 sm:px-4 my-6 sm:my-auto">
        
        {/* Top Feature Pill */}
        <div className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[11px] sm:text-xs font-medium mb-4 sm:mb-6 transition-colors duration-300 ${
          isDark 
            ? 'bg-[#09161E]/90 border border-emerald-500/30 text-slate-300 shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
            : 'bg-white border border-teal-200 text-teal-800 shadow-nova-sm'
        }`}>
          <span className="w-2 h-2 rounded-full bg-[#34D399] animate-pulse" />
          <span className="truncate">AI-powered • Developer focused • Beginner friendly</span>
        </div>

        {/* Display Headline */}
        <h1 className={`text-3xl sm:text-5xl md:text-6xl lg:text-[62px] font-extrabold leading-[1.15] sm:leading-[1.12] tracking-tight mb-4 sm:mb-5 transition-colors ${
          isDark ? 'text-white' : 'text-slate-900'
        }`}>
          Your first open source <br className="hidden xs:inline" />
          contribution <span className="text-[#34D399] drop-shadow-[0_0_20px_rgba(52,211,153,0.4)]">starts here.</span>
        </h1>

        {/* Subtitle */}
        <p className={`text-xs sm:text-base md:text-lg leading-relaxed max-w-2xl mx-auto mb-6 sm:mb-8 transition-colors px-2 ${
          isDark ? 'text-slate-400' : 'text-slate-600'
        }`}>
          GitNova finds real GitHub issues that match your skills, explains what needs to be done, and guides you to your first pull request.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 w-full sm:w-auto px-4 sm:px-0">
          <Link
            to="/onboarding"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3 sm:py-3.5 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#042F2C] rounded-2xl text-xs sm:text-sm font-extrabold transition-all shadow-[0_0_20px_rgba(159,232,195,0.35)] hover:scale-[1.02]"
          >
            <span>Find My First Issue</span>
            <ArrowRight className="w-4 h-4 stroke-[2.5]" />
          </Link>

          <Link
            to="/issues"
            className={`w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3 sm:py-3.5 rounded-2xl text-xs sm:text-sm font-bold transition-all ${
              isDark 
                ? 'bg-[#09151D]/90 hover:bg-[#10232E] border border-slate-700/60 text-slate-200' 
                : 'bg-white hover:bg-slate-50 border border-slate-300 text-slate-800 shadow-nova-sm'
            }`}
          >
            <span>I'm new to open source</span>
          </Link>
        </div>

      </main>

      {/* 3. Bottom Feature Cards Box & Footer */}
      <footer className="w-full max-w-5xl mx-auto z-20 shrink-0 space-y-3 sm:space-y-4 pb-2 sm:pb-0">
        
        {/* 3 Feature Steps Unified Glass Container */}
        <div 
          id="how-it-works"
          className={`w-full rounded-2xl sm:rounded-3xl p-4 sm:p-6 grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 text-left transition-all duration-300 ${
            isDark 
              ? 'bg-[#081218]/90 border border-slate-800/80 shadow-[0_8px_25px_rgba(0,0,0,0.5)]' 
              : 'bg-white border border-slate-200/90 shadow-nova-md'
          }`}
        >
          {/* Step 01: Find */}
          <div className="space-y-1.5 sm:space-y-2">
            <div className="flex items-center justify-between">
              <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex items-center justify-center border transition-colors ${
                isDark ? 'bg-[#0B1820] border-slate-800 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'
              }`}>
                <Search className="w-4 h-4 text-[#34D399]" />
              </div>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                isDark ? 'border-emerald-500/30 text-[#34D399] bg-[#061A16]' : 'border-teal-200 text-teal-700 bg-teal-50'
              }`}>
                01
              </span>
            </div>
            <div>
              <h3 className={`text-xs sm:text-sm font-bold mb-0.5 transition-colors ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Find
              </h3>
              <p className={`text-[11px] leading-relaxed transition-colors ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                We scan thousands of repositories and handpick issues that fit your level.
              </p>
            </div>
          </div>

          {/* Step 02: Understand */}
          <div className="space-y-1.5 sm:space-y-2">
            <div className="flex items-center justify-between">
              <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex items-center justify-center border transition-colors ${
                isDark ? 'bg-[#0B1820] border-slate-800 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'
              }`}>
                <BookOpen className="w-4 h-4 text-[#34D399]" />
              </div>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                isDark ? 'border-emerald-500/30 text-[#34D399] bg-[#061A16]' : 'border-teal-200 text-teal-700 bg-teal-50'
              }`}>
                02
              </span>
            </div>
            <div>
              <h3 className={`text-xs sm:text-sm font-bold mb-0.5 transition-colors ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Understand
              </h3>
              <p className={`text-[11px] leading-relaxed transition-colors ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                We break down the issue, show you the code, and what needs to change.
              </p>
            </div>
          </div>

          {/* Step 03: Contribute */}
          <div className="space-y-1.5 sm:space-y-2">
            <div className="flex items-center justify-between">
              <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex items-center justify-center border transition-colors ${
                isDark ? 'bg-[#0B1820] border-slate-800 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'
              }`}>
                <Rocket className="w-4 h-4 text-[#34D399]" />
              </div>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                isDark ? 'border-emerald-500/30 text-[#34D399] bg-[#061A16]' : 'border-teal-200 text-teal-700 bg-teal-50'
              }`}>
                03
              </span>
            </div>
            <div>
              <h3 className={`text-xs sm:text-sm font-bold mb-0.5 transition-colors ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Contribute
              </h3>
              <p className={`text-[11px] leading-relaxed transition-colors ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                Follow the step-by-step plan and open your first pull request.
              </p>
            </div>
          </div>
        </div>

        {/* Footer Pill */}
        <div className={`text-center flex items-center justify-center gap-2 text-[10px] sm:text-[11px] font-medium transition-colors ${
          isDark ? 'text-slate-400' : 'text-slate-600'
        }`}>
          <span className="text-[#34D399]">💚</span>
          <span className="truncate">Loved by developers • Beginner friendly • AI powered • Developer focused</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
