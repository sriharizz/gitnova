import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Layers, BookOpen, Bookmark, Activity, Sparkles, ChevronRight, User, Terminal, Compass, Sun, Moon, X } from 'lucide-react';
import GitNovaLogo from '../GitNovaLogo';
import { useTheme } from '../../lib/ThemeContext';

export const AppSidebar = ({ className = '', isOpen = false, onClose }) => {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const navItems = [
    { id: 'issues', label: 'Contribution Feed', path: '/issues', icon: Compass },
    { id: 'learn', label: 'Stack Preferences', path: '/onboarding', icon: Sparkles },
    { id: 'bookmarks', label: 'Saved Issues', path: '#', icon: Bookmark, badge: 'Soon' },
    { id: 'activity', label: 'Journey History', path: '#', icon: Activity, badge: 'Soon' },
  ];

  // Read active preferences
  const userPrefs = (() => {
    try {
      const saved = localStorage.getItem('gitnova_user_preferences');
      return saved ? JSON.parse(saved) : { languages: ['Python'], difficulty: 'BEGINNER' };
    } catch {
      return { languages: ['Python'], difficulty: 'BEGINNER' };
    }
  })();

  const primaryLang = userPrefs.languages?.[0] || 'Python';
  const userDiff = userPrefs.difficulty || 'BEGINNER';

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-200"
          aria-hidden="true"
        />
      )}

      {/* Main Sidebar Container (Desktop Sticky + Mobile Drawer) */}
      <aside
        className={`w-64 flex flex-col justify-between shrink-0 h-screen p-5
          bg-white dark:bg-[#08131A]
          border-r border-slate-200/90 dark:border-slate-800
          transition-transform duration-300 ease-in-out z-50
          fixed md:sticky top-0 inset-y-0 left-0
          ${isOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'}
          ${className}`}
      >
        <div>
          {/* Logo Header & Mobile Close Button */}
          <div className="flex items-center justify-between mb-8">
            <Link to="/" onClick={onClose} className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-xl bg-slate-900 dark:bg-slate-800 flex items-center justify-center shadow-nova-sm border border-slate-700 group-hover:border-teal-500/50 transition-colors">
                <GitNovaLogo className="w-5 h-5 text-teal-400" />
              </div>
              <div>
                <span className="font-extrabold text-base tracking-tight text-slate-900 dark:text-slate-100 block leading-tight">
                  GitNova
                </span>
                <span className="text-[10px] font-mono text-teal-600 dark:text-teal-400 font-bold uppercase tracking-wider">
                  Contribution Mentor
                </span>
              </div>
            </Link>

            {onClose && (
              <button
                onClick={onClose}
                className="p-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white md:hidden"
                aria-label="Close menu"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

        {/* Primary Nav List */}
        <nav className="space-y-1">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path) && item.path !== '#';

            return (
              <Link
                key={item.id}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2 rounded-xl font-medium text-xs transition-all duration-150 ${
                  isActive
                    ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-900 dark:text-teal-300 font-bold border border-teal-200 dark:border-teal-700/50 shadow-nova-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-obsidian-800 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-teal-600 dark:text-teal-400' : 'text-slate-400 dark:text-slate-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] uppercase font-mono font-bold text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-obsidian-700 px-1.5 py-0.5 rounded">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Footer */}
      <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-obsidian-700">

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium
            text-slate-600 dark:text-slate-400
            hover:bg-slate-50 dark:hover:bg-obsidian-800
            hover:text-slate-900 dark:hover:text-slate-100
            border border-transparent hover:border-slate-200 dark:hover:border-obsidian-700
            transition-all duration-150"
          aria-label="Toggle theme"
        >
          <div className="flex items-center gap-2.5">
            {isDark
              ? <Sun className="w-4 h-4 text-amber-400" />
              : <Moon className="w-4 h-4 text-slate-500" />
            }
            <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
          </div>
          <div className={`w-8 h-4 rounded-full flex items-center px-0.5 transition-colors duration-200
            ${isDark ? 'bg-teal-600' : 'bg-slate-300'}`}
          >
            <div className={`w-3 h-3 rounded-full bg-white shadow-sm transition-transform duration-200
              ${isDark ? 'translate-x-4' : 'translate-x-0'}`}
            />
          </div>
        </button>

        {/* User Profile Pill */}
        <Link
          to="/onboarding"
          className="flex items-center justify-between p-2.5 rounded-2xl transition-all shadow-nova-sm group
            bg-slate-50 dark:bg-obsidian-800
            hover:bg-slate-100/80 dark:hover:bg-obsidian-700
            border border-slate-200/90 dark:border-obsidian-600"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-xs shadow-nova-sm shrink-0">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">Active Profile</div>
              <div className="text-[10px] font-mono text-teal-700 dark:text-teal-400 font-semibold truncate">
                {primaryLang} · {userDiff}
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-300 group-hover:translate-x-0.5 transition-all shrink-0" />
        </Link>
      </div>
    </aside>
    </>
  );
};

export default AppSidebar;
