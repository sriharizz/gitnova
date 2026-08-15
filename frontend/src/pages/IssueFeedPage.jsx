import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, RefreshCw, SlidersHorizontal, Sparkles, Compass, Sun, Moon } from 'lucide-react';
import AppSidebar from '../components/layout/AppSidebar';
import IssueCard from '../components/common/IssueCard';
import { fetchRecommendations } from '../lib/api';
import { useTheme } from '../lib/ThemeContext';

export const IssueFeedPage = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [difficulty, setDifficulty] = useState('All');
  const [language, setLanguage] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  // Load preferences from localStorage if available
  const [userPrefs, setUserPrefs] = useState(() => {
    const saved = localStorage.getItem('gitnova_user_preferences');
    return saved ? JSON.parse(saved) : { languages: ['Python'], domains: ['Web Development'], difficulty: 'BEGINNER' };
  });

  const loadFeed = async () => {
    setLoading(true);
    setError(null);
    try {
      let activeLanguages = language !== 'All' ? [language] : userPrefs.languages;
      let activeDifficulty = difficulty !== 'All' ? difficulty.toUpperCase() : (userPrefs.difficulty || 'BEGINNER');

      const recs = await fetchRecommendations({
        languages: activeLanguages,
        domains: userPrefs.domains,
        difficulty: activeDifficulty,
        limit: 20
      });
      setIssues(recs.issues || []);
    } catch (err) {
      console.error('[GitNova] Failed to load issue feed:', err);
      setError('Could not load issues. Check backend API connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeed();
  }, [difficulty, language, userPrefs]);

  const filteredIssues = issues.filter(issue => {
    const matchesSearch = !searchTerm || (
      issue.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      issue.repo_full_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    return matchesSearch;
  });

  const activePrefString = [
    userPrefs.languages?.join(', ') || 'Any Language',
    (difficulty !== 'All' ? difficulty : userPrefs.difficulty) || 'Beginner',
    userPrefs.domains?.slice(0, 2).join(', ')
  ].filter(Boolean).join(' · ');

  return (
    <div className={`flex h-screen font-sans overflow-hidden transition-colors duration-300 ${
      isDark ? 'bg-[#050B0E] text-white' : 'bg-[#F8FAFC] text-slate-900'
    }`}>
      {/* App Sidebar Navigation */}
      <AppSidebar />

      {/* Main Issue Discovery Workspace */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto custom-scrollbar">
        {/* Top Header Bar */}
        <header className={`border-b px-6 sm:px-8 py-3.5 sticky top-0 z-10 flex items-center justify-between shrink-0 backdrop-blur-md transition-colors ${
          isDark 
            ? 'bg-[#050B0E]/90 border-slate-800' 
            : 'bg-white/90 border-slate-200'
        }`}>
          <div>
            <h1 className={`text-lg font-extrabold tracking-tight flex items-center gap-2 ${
              isDark ? 'text-white' : 'text-slate-900'
            }`}>
              <Compass className="w-5 h-5 text-[#34D399]" />
              <span>Contribution Feed</span>
            </h1>
            <p className={`text-xs font-medium mt-0.5 ${
              isDark ? 'text-slate-400' : 'text-slate-500'
            }`}>
              Verified, beginner-friendly open-source opportunities tailored to your stack.
            </p>
          </div>

          {/* Top Search Bar & Theme Switcher */}
          <div className="flex items-center gap-3">
            <div className="relative hidden sm:block w-64 md:w-72">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search issues, repos, topics..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`w-full pl-9 pr-3 py-1.5 rounded-xl text-xs placeholder-slate-400 focus:outline-none transition-all font-medium border ${
                  isDark 
                    ? 'bg-[#09161E] border-slate-700 text-white focus:border-emerald-500' 
                    : 'bg-slate-50 border-slate-200 text-slate-800 focus:border-teal-500'
                }`}
              />
            </div>

            <button
              onClick={toggleTheme}
              className={`p-2 rounded-xl border transition-all ${
                isDark 
                  ? 'bg-[#09151D] border-slate-700 text-amber-300 hover:bg-[#0E202B]' 
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
              title={`Switch to ${isDark ? 'Light' : 'Dark'} mode`}
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        {/* User Preferences Active Summary Banner */}
        <div className="px-6 sm:px-8 pt-4 pb-1">
          <div className={`rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 border transition-colors ${
            isDark 
              ? 'bg-[#08131A] border-slate-800 shadow-sm' 
              : 'bg-white border-slate-200 shadow-nova-sm'
          }`}>
            <div className="flex items-center gap-3">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${
                isDark 
                  ? 'bg-[#071F1B] border-emerald-500/30 text-[#34D399]' 
                  : 'bg-teal-50 border-teal-200 text-teal-700'
              }`}>
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Personalized for:</span>
                <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-md border ${
                  isDark 
                    ? 'bg-[#0D1E28] text-slate-200 border-slate-700' 
                    : 'bg-slate-100 text-slate-800 border-slate-200'
                }`}>
                  {activePrefString}
                </span>
              </div>
            </div>

            <button
              onClick={() => navigate('/onboarding')}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-colors shrink-0 ${
                isDark 
                  ? 'bg-[#0D1E28] border-slate-700 text-slate-300 hover:bg-[#122836]' 
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <SlidersHorizontal className="w-3 h-3 text-slate-400" />
              <span>Customize Stack</span>
            </button>
          </div>
        </div>

        {/* Filter Pills Row */}
        <div className="px-6 sm:px-8 pt-3 pb-2 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mr-1.5">Difficulty:</span>

            {['All', 'Beginner', 'Intermediate', 'Advanced'].map(diff => (
              <button
                key={diff}
                onClick={() => setDifficulty(diff)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
                  difficulty === diff
                    ? (isDark 
                        ? 'bg-[#9FE8C3] text-[#064E3B] border-[#9FE8C3] font-bold shadow-sm' 
                        : 'bg-teal-700 text-white border-teal-700 shadow-nova-sm')
                    : (isDark 
                        ? 'bg-[#08131A] text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white' 
                        : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50')
                }`}
              >
                {diff === 'All' ? 'Preferred Tier' : diff}
              </button>
            ))}
          </div>

          <div className={`flex items-center gap-1.5 text-xs font-medium ${
            isDark ? 'text-slate-400' : 'text-slate-500'
          }`}>
            <span className="w-2 h-2 rounded-full bg-[#34D399] animate-pulse" />
            <span>{filteredIssues.length} verified opportunities</span>
          </div>
        </div>

        {/* Issues Grid */}
        <div className="px-6 sm:px-8 py-3 pb-12">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <RefreshCw className="w-8 h-8 text-[#34D399] animate-spin mb-3" />
              <p className={`text-xs font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Fetching AST-verified issues...
              </p>
            </div>
          ) : error ? (
            <div className={`p-6 rounded-2xl border text-center my-6 ${
              isDark ? 'bg-[#180D0D] border-red-900/50 text-red-300' : 'bg-red-50 border-red-200 text-red-800'
            }`}>
              <p className="text-xs font-semibold mb-2">{error}</p>
              <button 
                onClick={loadFeed}
                className="px-4 py-1.5 bg-red-600 text-white rounded-xl text-xs font-bold"
              >
                Retry
              </button>
            </div>
          ) : filteredIssues.length === 0 ? (
            <div className={`p-10 rounded-2xl border text-center my-6 ${
              isDark ? 'bg-[#08131A] border-slate-800 text-slate-400' : 'bg-white border-slate-200 text-slate-500'
            }`}>
              <p className="text-sm font-semibold mb-1">No matching issues found</p>
              <p className="text-xs text-slate-400">Try adjusting your filters or search keywords.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredIssues.map(issue => (
                <IssueCard
                  key={issue.id}
                  issue={issue}
                  onSelect={(id) => navigate(`/issues/${id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default IssueFeedPage;
