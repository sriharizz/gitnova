import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowRight, Check, Globe, Database, Brain, Wrench, Layers, Sun, Moon, Sparkles, Terminal, Cpu, Code2 } from 'lucide-react';
import GitNovaLogo from '../components/GitNovaLogo';
import { saveUserPreferences } from '../lib/api';
import { useTheme } from '../lib/ThemeContext';

export const OnboardingPage = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const [isSaving, setIsSaving] = useState(false);

  // Preference Dimensions (Single-Page Form State)
  const [selectedLanguage, setSelectedLanguage] = useState('Python');
  const [selectedInterest, setSelectedInterest] = useState('Web / Backend');
  const [selectedExperience, setSelectedExperience] = useState('Beginner');

  const languageOptions = [
    {
      id: 'Python',
      name: 'Python',
      icon: '🐍',
      tag: 'AI & Data Science',
      desc: 'PyTorch, Scikit-learn, Click, Haystack, FastAPI'
    },
    {
      id: 'TypeScript / JavaScript',
      name: 'TypeScript / JavaScript',
      icon: '🔷',
      tag: 'Web & Fullstack',
      desc: 'React, Express, Vite, Node.js, Kimi Code'
    },
    {
      id: 'Java',
      name: 'Java',
      icon: '☕',
      tag: 'Enterprise & Systems',
      desc: 'Spring, Apache Beam, Kestra, Nacos, Sedona'
    },
    {
      id: 'Go',
      name: 'Go',
      icon: '🐹',
      tag: 'Cloud & Infrastructure',
      desc: 'Kubescape, K0s, Zitadel OIDC, Gin, Elastic'
    }
  ];

  const interestOptions = [
    {
      id: 'Web / Backend',
      name: 'Web / Backend',
      icon: Globe,
      tag: 'APIs & Services',
      desc: 'FastAPI, Express, REST frameworks, HTTP middleware'
    },
    {
      id: 'AI / Machine Learning',
      name: 'AI / Machine Learning',
      icon: Brain,
      tag: 'Models & RAG',
      desc: 'LLMs, Transformers, Haystack, Unsloth, Agentic pipelines'
    },
    {
      id: 'Data / Analytics',
      name: 'Data / Analytics',
      icon: Layers,
      tag: 'Pipelines & ML',
      desc: 'Scikit-learn, Apache Beam, Doris, Pandas, Stream processing'
    },
    {
      id: 'Developer Tools / Automation',
      name: 'Developer Tools / Automation',
      icon: Wrench,
      tag: 'CLIs & DevOps',
      desc: 'Command-line tools, Linters, CI/CD, Microcks, Security'
    }
  ];

  const experienceOptions = [
    {
      id: 'Beginner',
      title: 'Beginner Contributor',
      tag: 'First PR Friendly',
      desc: 'Approach-verified, isolated fixes with clear test guidance and zero architectural friction.'
    },
    {
      id: 'Intermediate',
      title: 'Intermediate Contributor',
      tag: 'Multi-File Scope',
      desc: 'Feature extensions, cross-file bug fixes, and broader component integrations.'
    },
    {
      id: 'Advanced',
      title: 'Advanced Contributor',
      tag: 'Deep Architecture',
      desc: 'Core algorithm overhauls, async infrastructure, and performance optimizations.'
    }
  ];

  const handleFindIssues = async () => {
    setIsSaving(true);

    let langArray = [];
    if (selectedLanguage === 'TypeScript / JavaScript') {
      langArray = ['TypeScript', 'JavaScript'];
    } else {
      langArray = [selectedLanguage];
    }

    let domainArray = [];
    if (selectedInterest === 'Web / Backend') {
      domainArray = ['Web Development', 'Backend Development', 'web', 'backend'];
    } else if (selectedInterest === 'AI / Machine Learning') {
      domainArray = ['AI / Machine Learning', 'ai', 'machine learning', 'ml'];
    } else if (selectedInterest === 'Data / Analytics') {
      domainArray = ['Data Science', 'Data Analytics', 'data', 'analytics'];
    } else if (selectedInterest === 'Developer Tools / Automation') {
      domainArray = ['Developer Tools', 'DevOps', 'Automation', 'tools', 'cli'];
    } else {
      domainArray = [selectedInterest];
    }

    const preferences = {
      user_id: 'default_user',
      languages: langArray,
      domains: domainArray,
      difficulty: selectedExperience.toUpperCase()
    };

    localStorage.setItem('gitnova_user_preferences', JSON.stringify(preferences));

    try {
      await saveUserPreferences(preferences);
    } catch (err) {
      console.warn('[GitNova] Synced preferences locally (API unavailable):', err);
    } finally {
      setIsSaving(false);
      navigate('/issues');
    }
  };

  return (
    <div className={`min-h-screen w-full font-sans flex flex-col justify-between select-none px-4 py-4 sm:px-8 sm:py-6 lg:px-16 transition-colors duration-300 relative overflow-x-hidden ${
      isDark 
        ? 'bg-gradient-to-b from-[#050D13] via-[#081722] to-[#040A0F] text-white' 
        : 'bg-gradient-to-b from-[#F8FAFC] via-[#F1F5F9] to-[#E2E8F0] text-slate-900'
    }`}>
      
      {/* Deep Luminous Cosmic Glow Backdrops */}
      <div className={`absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[300px] sm:w-[900px] sm:h-[550px] lg:w-[1300px] lg:h-[750px] rounded-full blur-[100px] sm:blur-[150px] -z-10 pointer-events-none ${
        isDark 
          ? 'bg-gradient-to-tr from-emerald-500/15 via-teal-400/20 to-cyan-500/15' 
          : 'bg-gradient-to-tr from-teal-500/10 via-emerald-400/15 to-cyan-500/10'
      }`} />

      {/* Top Navbar */}
      <header className="w-full max-w-6xl mx-auto flex items-center justify-between z-20 shrink-0 pb-4">
        <Link to="/" className="flex items-center gap-2.5 group">
          <GitNovaLogo className="w-7 h-7 sm:w-8 sm:h-8" static={true} />
          <span className={`font-extrabold text-xl sm:text-2xl tracking-tight transition-colors ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            GitNova
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-xl border transition-all ${
              isDark 
                ? 'bg-[#09151D] border-slate-700 text-amber-300 hover:bg-[#0E202B]' 
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100 shadow-sm'
            }`}
            title={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Main Single-Page Preference Workspace */}
      <main className="w-full max-w-6xl mx-auto flex-1 flex flex-col justify-center py-4 z-10">
        
        {/* Header Title */}
        <div className="text-center max-w-2xl mx-auto mb-6 sm:mb-8">
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold mb-3 border ${
            isDark 
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
              : 'bg-teal-50 border-teal-200 text-teal-700'
          }`}>
            <Sparkles className="w-3.5 h-3.5" />
            <span>One-Step Contributor Onboarding</span>
          </div>
          <h1 className={`text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight mb-2 ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            Configure Your Contribution Preferences
          </h1>
          <p className={`text-xs sm:text-sm font-medium ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Select your language, interest domain, and experience level to instantly find your ideal PR.
          </p>
        </div>

        {/* Unified 3-Section Grid */}
        <div className="space-y-6 sm:space-y-8">
          
          {/* Section 1: LANGUAGE */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-5 h-5 rounded-full text-[11px] font-extrabold flex items-center justify-center ${
                isDark ? 'bg-emerald-500/20 text-emerald-300' : 'bg-teal-100 text-teal-800'
              }`}>
                1
              </span>
              <h2 className={`text-xs sm:text-sm font-bold uppercase tracking-wider ${
                isDark ? 'text-slate-200' : 'text-slate-800'
              }`}>
                Select Primary Language
              </h2>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {languageOptions.map(lang => {
                const isSelected = selectedLanguage === lang.id;
                return (
                  <button
                    key={lang.id}
                    type="button"
                    onClick={() => setSelectedLanguage(lang.id)}
                    className={`relative text-left p-3.5 rounded-2xl border transition-all flex flex-col justify-between ${
                      isSelected
                        ? isDark
                          ? 'bg-[#0E2A27] border-[#34D399] shadow-[0_0_20px_rgba(52,211,153,0.15)] ring-1 ring-[#34D399]'
                          : 'bg-teal-50/80 border-teal-600 shadow-sm ring-1 ring-teal-600'
                        : isDark
                          ? 'bg-[#08151D]/80 border-slate-800 hover:border-slate-700 hover:bg-[#0C1E2A]'
                          : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50 shadow-sm'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xl">{lang.icon}</span>
                      {isSelected ? (
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                          isDark ? 'bg-[#34D399] text-[#050D13]' : 'bg-teal-600 text-white'
                        }`}>
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      ) : (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                          isDark ? 'bg-[#050D13] border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-500'
                        }`}>
                          {lang.tag}
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 className={`font-bold text-sm sm:text-base ${
                        isSelected ? (isDark ? 'text-white' : 'text-teal-950') : (isDark ? 'text-slate-200' : 'text-slate-800')
                      }`}>
                        {lang.name}
                      </h3>
                      <p className={`text-[11px] mt-0.5 line-clamp-2 ${
                        isDark ? 'text-slate-400' : 'text-slate-500'
                      }`}>
                        {lang.desc}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section 2: INTEREST */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-5 h-5 rounded-full text-[11px] font-extrabold flex items-center justify-center ${
                isDark ? 'bg-emerald-500/20 text-emerald-300' : 'bg-teal-100 text-teal-800'
              }`}>
                2
              </span>
              <h2 className={`text-xs sm:text-sm font-bold uppercase tracking-wider ${
                isDark ? 'text-slate-200' : 'text-slate-800'
              }`}>
                Select Core Interest
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {interestOptions.map(interest => {
                const isSelected = selectedInterest === interest.id;
                const IconComponent = interest.icon;
                return (
                  <button
                    key={interest.id}
                    type="button"
                    onClick={() => setSelectedInterest(interest.id)}
                    className={`relative text-left p-3.5 rounded-2xl border transition-all flex flex-col justify-between ${
                      isSelected
                        ? isDark
                          ? 'bg-[#0E2A27] border-[#34D399] shadow-[0_0_20px_rgba(52,211,153,0.15)] ring-1 ring-[#34D399]'
                          : 'bg-teal-50/80 border-teal-600 shadow-sm ring-1 ring-teal-600'
                        : isDark
                          ? 'bg-[#08151D]/80 border-slate-800 hover:border-slate-700 hover:bg-[#0C1E2A]'
                          : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50 shadow-sm'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className={`p-2 rounded-xl border ${
                        isSelected 
                          ? isDark ? 'bg-[#34D399]/20 border-[#34D399]/40 text-[#34D399]' : 'bg-teal-100 border-teal-300 text-teal-800'
                          : isDark ? 'bg-[#050D13] border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-600'
                      }`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      {isSelected && (
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                          isDark ? 'bg-[#34D399] text-[#050D13]' : 'bg-teal-600 text-white'
                        }`}>
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      )}
                    </div>
                    <div>
                      <h3 className={`font-bold text-sm sm:text-base ${
                        isSelected ? (isDark ? 'text-white' : 'text-teal-950') : (isDark ? 'text-slate-200' : 'text-slate-800')
                      }`}>
                        {interest.name}
                      </h3>
                      <p className={`text-[11px] mt-0.5 line-clamp-2 ${
                        isDark ? 'text-slate-400' : 'text-slate-500'
                      }`}>
                        {interest.desc}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section 3: EXPERIENCE */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className={`w-5 h-5 rounded-full text-[11px] font-extrabold flex items-center justify-center ${
                isDark ? 'bg-emerald-500/20 text-emerald-300' : 'bg-teal-100 text-teal-800'
              }`}>
                3
              </span>
              <h2 className={`text-xs sm:text-sm font-bold uppercase tracking-wider ${
                isDark ? 'text-slate-200' : 'text-slate-800'
              }`}>
                Select Experience Level
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {experienceOptions.map(exp => {
                const isSelected = selectedExperience === exp.id;
                return (
                  <button
                    key={exp.id}
                    type="button"
                    onClick={() => setSelectedExperience(exp.id)}
                    className={`relative text-left p-3.5 rounded-2xl border transition-all flex flex-col justify-between ${
                      isSelected
                        ? isDark
                          ? 'bg-[#0E2A27] border-[#34D399] shadow-[0_0_20px_rgba(52,211,153,0.15)] ring-1 ring-[#34D399]'
                          : 'bg-teal-50/80 border-teal-600 shadow-sm ring-1 ring-teal-600'
                        : isDark
                          ? 'bg-[#08151D]/80 border-slate-800 hover:border-slate-700 hover:bg-[#0C1E2A]'
                          : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50 shadow-sm'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                        isSelected 
                          ? isDark ? 'bg-[#34D399]/20 border-[#34D399]/40 text-[#34D399]' : 'bg-teal-100 border-teal-300 text-teal-800'
                          : isDark ? 'bg-[#050D13] border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-500'
                      }`}>
                        {exp.tag}
                      </span>
                      {isSelected && (
                        <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                          isDark ? 'bg-[#34D399] text-[#050D13]' : 'bg-teal-600 text-white'
                        }`}>
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      )}
                    </div>
                    <div>
                      <h3 className={`font-bold text-sm sm:text-base ${
                        isSelected ? (isDark ? 'text-white' : 'text-teal-950') : (isDark ? 'text-slate-200' : 'text-slate-800')
                      }`}>
                        {exp.title}
                      </h3>
                      <p className={`text-[11px] mt-0.5 ${
                        isDark ? 'text-slate-400' : 'text-slate-500'
                      }`}>
                        {exp.desc}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* Action Button CTA Bar */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-800/60">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Sparkles className="w-4 h-4 text-[#34D399]" />
            <span>Personalized recommendation engine ready across 153 indexed repositories.</span>
          </div>

          <button
            type="button"
            disabled={isSaving}
            onClick={handleFindIssues}
            className={`w-full sm:w-auto px-8 py-3.5 rounded-2xl font-extrabold text-sm sm:text-base flex items-center justify-center gap-2.5 transition-all shadow-lg cursor-pointer ${
              isDark
                ? 'bg-gradient-to-r from-emerald-500 to-teal-400 text-slate-950 hover:from-emerald-400 hover:to-teal-300 shadow-[0_4px_25px_rgba(52,211,153,0.3)]'
                : 'bg-teal-600 text-white hover:bg-teal-700 shadow-teal-600/30'
            }`}
          >
            <span>{isSaving ? 'Configuring Feed...' : 'Find my issues'}</span>
            <ArrowRight className="w-4 h-4 stroke-[2.5]" />
          </button>
        </div>

      </main>

      {/* Footer */}
      <footer className="w-full max-w-6xl mx-auto flex items-center justify-between text-[11px] text-slate-500 py-3 shrink-0">
        <div>GitNova v4.4 — Autonomous Open Source Mentor</div>
        <div>AST-Verified & Grounded</div>
      </footer>
    </div>
  );
};

export default OnboardingPage;
