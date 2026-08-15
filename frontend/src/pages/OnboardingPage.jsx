import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowRight, ArrowLeft, Check, Globe, Database, Brain, Monitor, Smartphone, Wrench, Layers, Sun, Moon, Sparkles } from 'lucide-react';
import GitNovaLogo from '../components/GitNovaLogo';
import StepperProgress from '../components/common/StepperProgress';
import { saveUserPreferences } from '../lib/api';
import { useTheme } from '../lib/ThemeContext';

export const OnboardingPage = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const [currentStep, setCurrentStep] = useState(1);
  const [isSaving, setIsSaving] = useState(false);

  // Step 1: Tech Stack
  const [selectedTech, setSelectedTech] = useState(['Python', 'JavaScript']);
  // Step 2: Experience Level
  const [selectedExperience, setSelectedExperience] = useState('Beginner');
  // Step 3: Interests
  const [selectedInterests, setSelectedInterests] = useState(['Web Development', 'AI / Machine Learning']);

  const techStackList = [
    { id: 'Python', name: 'Python', icon: '🐍', tag: 'AI & Backend' },
    { id: 'JavaScript', name: 'JavaScript', icon: '🟨', tag: 'Web & Fullstack' },
    { id: 'TypeScript', name: 'TypeScript', icon: '🔷', tag: 'Typed Web' },
    { id: 'Java', name: 'Java', icon: '☕', tag: 'Enterprise & Android' },
    { id: 'C++', name: 'C++', icon: '⚡', tag: 'Systems & Performance' },
    { id: 'Go', name: 'Go', icon: '🐹', tag: 'Cloud & Microservices' },
    { id: 'Rust', name: 'Rust', icon: '🦀', tag: 'Memory Safety & Core' },
    { id: 'C#', name: 'C#', icon: '💜', tag: '.NET & Game Dev' },
    { id: 'Dart', name: 'Dart', icon: '🎯', tag: 'Flutter & Mobile' },
    { id: 'PHP', name: 'PHP', icon: '🐘', tag: 'Web & CMS' },
    { id: 'Ruby', name: 'Ruby', icon: '💎', tag: 'Rails & Scripting' },
    { id: 'Kotlin', name: 'Kotlin', icon: '🪟', tag: 'Android & Modern JVM' }
  ];

  const experienceList = [
    { 
      id: 'Beginner', 
      title: 'Beginner Contributor', 
      desc: 'New to open source or looking for approachable, highly isolated tasks with step-by-step guidance and zero architectural risk.',
      tag: 'First PR Friendly',
      recommendedFor: 'Documentation, typo fixes, isolated helper functions'
    },
    { 
      id: 'Intermediate', 
      title: 'Intermediate Contributor', 
      desc: 'Comfortable with Git workflows, multi-file codebases, running unit test suites, and handling refactors or bug fixes.',
      tag: 'Multi-File Focus',
      recommendedFor: 'Bug fixes, new feature options, test coverage'
    },
    { 
      id: 'Advanced', 
      title: 'Advanced Contributor', 
      desc: 'Experienced engineer seeking major subsystem architectural improvements, performance tuning, or core algorithm overhauls.',
      tag: 'Architecture Level',
      recommendedFor: 'Subsystem refactoring, async pipelines, core internals'
    }
  ];

  const interestList = [
    { id: 'AI / Machine Learning', name: 'AI / Machine Learning', icon: Brain, desc: 'PyTorch, Transformers, LLMs, LangChain', count: '140+ repos' },
    { id: 'Web Development', name: 'Web Development', icon: Globe, desc: 'React, Vue, Fastify, Next.js, Vite', count: '280+ repos' },
    { id: 'Backend Development', name: 'Backend Development', icon: Database, desc: 'Node.js, Flask, FastAPI, Go, Django', count: '210+ repos' },
    { id: 'Data Science', name: 'Data Science & Analysis', icon: Layers, desc: 'Pandas, NumPy, Scikit-learn, Polars', count: '95+ repos' },
    { id: 'DevOps', name: 'DevOps & Cloud Infra', icon: Monitor, desc: 'Docker, Kubernetes, GitHub Actions, CI/CD', count: '120+ repos' },
    { id: 'Mobile Development', name: 'Mobile Apps', icon: Smartphone, desc: 'React Native, Flutter, Kotlin, Swift', count: '85+ repos' },
    { id: 'Databases', name: 'Databases & Storage', icon: Database, desc: 'PostgreSQL, Redis, Supabase, SQLite', count: '70+ repos' },
    { id: 'Developer Tools', name: 'Developer Tools & CLIs', icon: Wrench, desc: 'Linters, Compilers, Bundlers, Parsers', count: '160+ repos' }
  ];

  const toggleTech = (id) => {
    setSelectedTech(prev => prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]);
  };

  const toggleInterest = (id) => {
    setSelectedInterests(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const handleFinishOnboarding = async () => {
    setIsSaving(true);
    const preferences = {
      user_id: 'default_user',
      languages: selectedTech,
      domains: selectedInterests,
      difficulty: selectedExperience.toUpperCase()
    };
    localStorage.setItem('gitnova_user_preferences', JSON.stringify(preferences));

    try {
      await saveUserPreferences(preferences);
    } catch (err) {
      console.warn('[GitNova] Failed to sync preferences to Supabase, localStorage active:', err);
    } finally {
      setIsSaving(false);
      navigate('/issues');
    }
  };

  const stepperSteps = [
    { id: 1, label: 'Tech Stack' },
    { id: 2, label: 'Experience Level' },
    { id: 3, label: 'Domain Topics' }
  ];

  return (
    <div className={`h-screen max-h-screen w-full font-sans flex flex-col justify-between select-none px-6 py-4 sm:px-10 sm:py-5 lg:px-16 lg:py-6 transition-colors duration-300 relative overflow-hidden ${
      isDark 
        ? 'bg-gradient-to-b from-[#050D13] via-[#081722] to-[#040A0F] text-white' 
        : 'bg-gradient-to-b from-[#F8FAFC] via-[#F1F5F9] to-[#E2E8F0] text-slate-900'
    }`}>
      
      {/* Deep Luminous Cosmic Glow Backdrops */}
      <div className={`absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[550px] lg:w-[1300px] lg:h-[750px] rounded-full blur-[150px] -z-10 pointer-events-none ${
        isDark 
          ? 'bg-gradient-to-tr from-emerald-500/20 via-teal-400/25 to-cyan-500/15' 
          : 'bg-gradient-to-tr from-teal-500/10 via-emerald-400/15 to-cyan-500/10'
      }`} />

      {/* 1. Top Navigation Bar */}
      <header className="w-full max-w-6xl mx-auto flex items-center justify-between z-30 shrink-0">
        <Link to="/" className="flex items-center gap-3 group">
          <GitNovaLogo className="w-8 h-8 sm:w-9 sm:h-9" static={true} />
          <span className={`font-extrabold text-xl sm:text-2xl tracking-tight transition-colors ${
            isDark ? 'text-white' : 'text-slate-900'
          }`}>
            GitNova
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className={`p-2 sm:p-2.5 rounded-xl border transition-all ${
              isDark 
                ? 'bg-[#091B27]/90 border-slate-700/80 text-amber-300 hover:bg-[#0E283A] shadow-sm' 
                : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100 shadow-sm'
            }`}
            title={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <button 
            onClick={() => navigate('/issues')}
            className={`text-xs font-bold px-4 py-2 rounded-xl transition-all border ${
              isDark 
                ? 'bg-[#091B27]/90 border-slate-700/80 text-slate-300 hover:text-white hover:bg-[#0E283A] shadow-sm' 
                : 'bg-white border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-sm'
            }`}
          >
            Skip for now
          </button>
        </div>
      </header>

      {/* 2. Main Expanded Preferences Canvas */}
      <main className="w-full max-w-6xl mx-auto flex-1 flex flex-col justify-center z-10 py-2 min-h-0">
        
        {/* Stepper Progress Centered */}
        <div className="flex justify-center mb-3.5 shrink-0">
          <StepperProgress steps={stepperSteps} currentStep={currentStep} onStepClick={setCurrentStep} />
        </div>

        {/* Large Elegant Glassmorphism Card */}
        <div className={`w-full rounded-3xl p-6 sm:p-8 lg:p-10 transition-all duration-300 shrink min-h-0 flex flex-col justify-between ${
          isDark 
            ? 'bg-[#0A1A26]/85 backdrop-blur-2xl border border-slate-700/60 shadow-[0_25px_80px_rgba(0,0,0,0.7)] ring-1 ring-white/5' 
            : 'bg-white/95 border border-slate-200/90 shadow-2xl backdrop-blur-sm'
        }`}>
          
          {/* STEP 1: Tech Stack */}
          {currentStep === 1 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="text-center max-w-2xl mx-auto space-y-1">
                <h1 className={`text-2xl sm:text-3xl font-extrabold tracking-tight transition-colors ${
                  isDark ? 'text-white' : 'text-slate-900'
                }`}>
                  What languages do you work with?
                </h1>
                <p className={`text-xs sm:text-sm leading-relaxed transition-colors ${
                  isDark ? 'text-slate-300' : 'text-slate-600'
                }`}>
                  Select all languages you want to contribute in. GitNova matches verified repositories tailored to your skills.
                </p>
              </div>

              {/* 4x3 Language Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {techStackList.map(tech => {
                  const isSelected = selectedTech.includes(tech.id);
                  return (
                    <button
                      key={tech.id}
                      onClick={() => toggleTech(tech.id)}
                      className={`p-3.5 sm:p-4 rounded-2xl border text-left transition-all duration-150 flex flex-col justify-between min-h-[78px] group relative ${
                        isSelected
                          ? (isDark 
                              ? 'bg-gradient-to-br from-[#064E3B]/70 via-[#07382D]/80 to-[#02281F]/90 border-2 border-[#34D399] text-white shadow-[0_0_20px_rgba(52,211,153,0.3)] ring-1 ring-[#34D399]/40' 
                              : 'bg-teal-50/90 border-2 border-teal-600 text-teal-950 ring-2 ring-teal-600/30 shadow-md')
                          : (isDark 
                              ? 'bg-[#0D212E]/70 border-slate-700/60 text-slate-200 hover:border-slate-500 hover:bg-[#112B3B]' 
                              : 'bg-slate-50/80 border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-white')
                      }`}
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2.5">
                          <span className="text-xl sm:text-2xl">{tech.icon}</span>
                          <span className="text-xs sm:text-sm font-bold tracking-tight">{tech.name}</span>
                        </div>
                        {isSelected && (
                          <div className={`w-4 h-4 sm:w-5 sm:h-5 rounded-full flex items-center justify-center shadow-sm ${
                            isDark ? 'bg-[#34D399] text-[#052E2B]' : 'bg-teal-700 text-white'
                          }`}>
                            <Check className="w-3 h-3 stroke-[3]" />
                          </div>
                        )}
                      </div>
                      <span className={`text-[11px] font-medium mt-1 transition-colors ${
                        isSelected 
                          ? (isDark ? 'text-[#34D399]' : 'text-teal-700') 
                          : (isDark ? 'text-slate-400' : 'text-slate-500')
                      }`}>
                        {tech.tag}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 2: Experience Level */}
          {currentStep === 2 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="text-center max-w-2xl mx-auto space-y-1">
                <h1 className={`text-2xl sm:text-3xl font-extrabold tracking-tight transition-colors ${
                  isDark ? 'text-white' : 'text-slate-900'
                }`}>
                  Select your contribution experience
                </h1>
                <p className={`text-xs sm:text-sm leading-relaxed transition-colors ${
                  isDark ? 'text-slate-300' : 'text-slate-600'
                }`}>
                  This calibrates our AST engine to enforce the Beginner Hard Gate and filter out risky repositories.
                </p>
              </div>

              {/* 3-Column Experience Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {experienceList.map(exp => {
                  const isSelected = selectedExperience === exp.id;
                  return (
                    <button
                      key={exp.id}
                      onClick={() => setSelectedExperience(exp.id)}
                      className={`p-5 sm:p-6 rounded-2xl border text-left transition-all duration-150 flex flex-col justify-between min-h-[185px] ${
                        isSelected
                          ? (isDark 
                              ? 'bg-gradient-to-br from-[#064E3B]/70 via-[#07382D]/80 to-[#02281F]/90 border-2 border-[#34D399] shadow-[0_0_25px_rgba(52,211,153,0.3)] ring-1 ring-[#34D399]/40 text-white' 
                              : 'bg-teal-50/90 border-2 border-teal-600 text-teal-950 ring-2 ring-teal-600/30 shadow-lg')
                          : (isDark 
                              ? 'bg-[#0D212E]/70 border-slate-700/60 text-slate-200 hover:border-slate-500 hover:bg-[#112B3B]' 
                              : 'bg-slate-50/80 border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-white')
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                            isDark 
                              ? 'bg-[#071F1A] border-emerald-500/40 text-[#34D399]' 
                              : 'bg-teal-100 border-teal-300 text-teal-900'
                          }`}>
                            {exp.tag}
                          </span>
                          {isSelected && (
                            <div className={`w-5 h-5 rounded-full flex items-center justify-center shadow-sm ${
                              isDark ? 'bg-[#34D399] text-[#052E2B]' : 'bg-teal-700 text-white'
                            }`}>
                              <Check className="w-3 h-3 stroke-[3]" />
                            </div>
                          )}
                        </div>

                        <h3 className={`text-base font-bold mb-1 transition-colors ${
                          isDark ? 'text-white' : 'text-slate-900'
                        }`}>
                          {exp.title}
                        </h3>

                        <p className={`text-xs leading-relaxed transition-colors ${
                          isDark ? 'text-slate-300' : 'text-slate-600'
                        }`}>
                          {exp.desc}
                        </p>
                      </div>

                      <div className={`pt-2.5 border-t text-[11px] font-medium mt-2 ${
                        isDark ? 'border-slate-700/60 text-slate-400' : 'border-slate-200 text-slate-500'
                      }`}>
                        <span className="font-bold text-slate-400">Best for:</span> {exp.recommendedFor}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 3: Domain Topics */}
          {currentStep === 3 && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="text-center max-w-2xl mx-auto space-y-1">
                <h1 className={`text-2xl sm:text-3xl font-extrabold tracking-tight transition-colors ${
                  isDark ? 'text-white' : 'text-slate-900'
                }`}>
                  What domain topics interest you?
                </h1>
                <p className={`text-xs sm:text-sm leading-relaxed transition-colors ${
                  isDark ? 'text-slate-300' : 'text-slate-600'
                }`}>
                  Choose the project domains you enjoy working on. You can adjust this anytime.
                </p>
              </div>

              {/* 4x2 Domain Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {interestList.map(interest => {
                  const Icon = interest.icon;
                  const isSelected = selectedInterests.includes(interest.id);
                  return (
                    <button
                      key={interest.id}
                      onClick={() => toggleInterest(interest.id)}
                      className={`p-3.5 sm:p-4 rounded-2xl border text-left transition-all duration-150 flex flex-col justify-between min-h-[105px] ${
                        isSelected
                          ? (isDark 
                              ? 'bg-gradient-to-br from-[#064E3B]/70 via-[#07382D]/80 to-[#02281F]/90 border-2 border-[#34D399] shadow-[0_0_20px_rgba(52,211,153,0.3)] ring-1 ring-[#34D399]/40 text-white' 
                              : 'bg-teal-50/90 border-2 border-teal-600 text-teal-950 ring-2 ring-teal-600/30 shadow-md')
                          : (isDark 
                              ? 'bg-[#0D212E]/70 border-slate-700/60 text-slate-200 hover:border-slate-500 hover:bg-[#112B3B]' 
                              : 'bg-slate-50/80 border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-white')
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className={`p-1.5 rounded-xl border ${
                          isDark 
                            ? 'bg-[#071F1B] border-emerald-500/30 text-[#34D399]' 
                            : 'bg-teal-100 border-teal-200 text-teal-800'
                        }`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        {isSelected && (
                          <div className={`w-4 h-4 sm:w-5 sm:h-5 rounded-full flex items-center justify-center shadow-sm ${
                            isDark ? 'bg-[#34D399] text-[#052E2B]' : 'bg-teal-700 text-white'
                          }`}>
                            <Check className="w-3 h-3 stroke-[3]" />
                          </div>
                        )}
                      </div>

                      <div>
                        <div className={`text-xs sm:text-sm font-bold truncate transition-colors ${
                          isDark ? 'text-white' : 'text-slate-900'
                        }`}>
                          {interest.name}
                        </div>
                        <span className={`text-[10px] font-mono mt-0.5 block ${
                          isDark ? 'text-slate-400' : 'text-slate-500'
                        }`}>
                          {interest.count}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Integrated Action Buttons */}
          <div className={`flex items-center justify-between pt-4 mt-4 border-t transition-colors ${
            isDark ? 'border-slate-700/60' : 'border-slate-200'
          }`}>
            {currentStep > 1 ? (
              <button
                onClick={() => setCurrentStep(prev => prev - 1)}
                className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border text-xs sm:text-sm font-bold transition-all ${
                  isDark 
                    ? 'bg-[#0D212E]/90 border-slate-700 text-slate-300 hover:bg-[#112B3B] hover:text-white' 
                    : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50 shadow-sm'
                }`}
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
            ) : <div />}

            {currentStep < 3 ? (
              <button
                onClick={() => setCurrentStep(prev => prev + 1)}
                className="inline-flex items-center gap-2 px-7 py-3 bg-gradient-to-r from-[#34D399] via-[#10B981] to-[#059669] hover:from-[#6EE7B7] hover:to-[#34D399] text-slate-950 font-extrabold rounded-2xl text-xs sm:text-sm transition-all shadow-[0_0_25px_rgba(52,211,153,0.45)] hover:shadow-[0_0_35px_rgba(52,211,153,0.65)] hover:scale-[1.02]"
              >
                <span>Continue</span>
                <ArrowRight className="w-4 h-4 stroke-[2.5]" />
              </button>
            ) : (
              <button
                onClick={handleFinishOnboarding}
                disabled={isSaving}
                className="inline-flex items-center gap-2.5 px-8 py-3 bg-gradient-to-r from-[#34D399] via-[#10B981] to-[#059669] hover:from-[#6EE7B7] hover:to-[#34D399] text-slate-950 font-extrabold rounded-2xl text-xs sm:text-sm transition-all shadow-[0_0_25px_rgba(52,211,153,0.45)] hover:shadow-[0_0_35px_rgba(52,211,153,0.65)] hover:scale-[1.02] disabled:opacity-75"
              >
                <span>{isSaving ? 'Finding Matches...' : 'Find Curated Issues'}</span>
                <ArrowRight className="w-4 h-4 stroke-[2.5]" />
              </button>
            )}
          </div>

        </div>
      </main>

      {/* 3. Footer */}
      <footer className={`w-full text-center py-2 flex items-center justify-center gap-1.5 text-[11px] font-medium shrink-0 z-20 transition-colors ${
        isDark ? 'text-slate-400' : 'text-slate-600'
      }`}>
        <span className="text-[#34D399]">💚</span>
        <span>Loved by developers • Beginner friendly • AI powered • Developer focused</span>
      </footer>
    </div>
  );
};

export default OnboardingPage;
