import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { RefreshCw, ArrowLeft, ExternalLink, Sun, Moon, Menu, Compass, ChevronRight, ChevronLeft } from 'lucide-react';
import JourneySidebar from '../components/layout/JourneySidebar';
import IssueOverviewView from '../components/workspace/IssueOverviewView';
import ContributionStatusView from '../components/workspace/ContributionStatusView';
import LearnConceptsView from '../components/workspace/LearnConceptsView';
import CodeExplorerView from '../components/workspace/CodeExplorerView';
import InvestigateView from '../components/workspace/InvestigateView';
import ContributionPlanView from '../components/workspace/ContributionPlanView';
import ImplementGuideView from '../components/workspace/ImplementGuideView';
import TestGuideView from '../components/workspace/TestGuideView';
import PreparePRView from '../components/workspace/PreparePRView';
import ReviewChecklistView from '../components/workspace/ReviewChecklistView';
import { fetchIssueById, fetchIssueCode, fetchIssueJourney } from '../lib/api';
import { useTheme } from '../lib/ThemeContext';

const STAGE_LABELS = {
  understand: '01 Understand',
  check_status: '02 Check Status',
  learn: '03 Learn Concepts',
  explore: '04 Explore Code',
  investigate: '05 Investigate',
  plan: '06 Plan Fix',
  implement: '07 Implement',
  test: '08 Test',
  prepare_pr: '09 Prepare PR',
  review: '10 Review'
};

export const IssueWorkspacePage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const [activeStep, setActiveStep] = useState('understand');
  const [completedSteps, setCompletedSteps] = useState(['understand']);
  const [isJourneyOpen, setIsJourneyOpen] = useState(false);

  const [issue, setIssue] = useState(null);
  const [journey, setJourney] = useState(null);
  const [codeData, setCodeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadIssueDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const issueRes = await fetchIssueById(id);
        setIssue(issueRes);

        try {
          const journeyRes = await fetchIssueJourney(id);
          setJourney(journeyRes);
        } catch (err) {
          console.warn('[GitNova] Journey endpoint warning:', err);
        }

        const codeRes = await fetchIssueCode(id);
        setCodeData(codeRes);
      } catch (err) {
        console.error('[GitNova] Failed to load issue workspace:', err);
        setError('GitNova couldn\'t load this contribution opportunity.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      loadIssueDetails();
    }
  }, [id]);

  const handleStepSelect = (stepId) => {
    setActiveStep(stepId);
    if (!completedSteps.includes(stepId)) {
      setCompletedSteps(prev => [...prev, stepId]);
    }
  };

  const nextStepMap = {
    understand: 'check_status',
    check_status: 'learn',
    learn: 'explore',
    explore: 'investigate',
    investigate: 'plan',
    plan: 'implement',
    implement: 'test',
    test: 'prepare_pr',
    prepare_pr: 'review'
  };

  const prevStepMap = {
    check_status: 'understand',
    learn: 'check_status',
    explore: 'learn',
    investigate: 'explore',
    plan: 'investigate',
    implement: 'plan',
    test: 'implement',
    prepare_pr: 'test',
    review: 'prepare_pr'
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-screen transition-colors ${
        isDark ? 'bg-[#050B0E] text-white' : 'bg-[#FAFAFA] text-slate-900'
      }`}>
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-[#34D399] animate-spin" />
          <p className="text-xs font-mono font-bold text-slate-400">Loading verified workspace context...</p>
        </div>
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className={`flex flex-col items-center justify-center h-screen p-6 text-center transition-colors ${
        isDark ? 'bg-[#050B0E] text-white' : 'bg-[#FAFAFA] text-slate-900'
      }`}>
        <h2 className="text-xl font-bold mb-2">Issue Not Found</h2>
        <p className="text-xs text-slate-400 mb-4">{error || "Could not retrieve precomputed issue data."}</p>
        <button
          onClick={() => navigate('/issues')}
          className="px-5 py-2.5 bg-[#9FE8C3] text-[#064E3B] rounded-xl text-xs font-bold transition-all"
        >
          Back to Issue Feed
        </button>
      </div>
    );
  }

  return (
    <div className={`flex h-screen font-sans overflow-hidden transition-colors ${
      isDark ? 'bg-[#050B0E] text-white' : 'bg-[#F8FAFC] text-slate-900'
    }`}>
      {/* Left 10-Stage Journey Sidebar (Desktop Sticky + Mobile Drawer) */}
      <JourneySidebar
        activeStep={activeStep}
        onSelectStep={handleStepSelect}
        completedSteps={completedSteps}
        isOpen={isJourneyOpen}
        onClose={() => setIsJourneyOpen(false)}
      />

      {/* Main Workspace Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto custom-scrollbar w-full min-w-0">
        {/* Top Sticky Breadcrumb & Stage Navigation Bar */}
        <header className={`px-4 sm:px-8 py-3 sticky top-0 z-10 flex items-center justify-between shrink-0 border-b backdrop-blur-md transition-colors ${
          isDark 
            ? 'bg-[#050B0E]/90 border-slate-800 text-white' 
            : 'bg-white/90 border-slate-200 text-slate-900'
        }`}>
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <button
              onClick={() => navigate('/issues')}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold transition-colors shrink-0 ${
                isDark ? 'text-slate-400 hover:text-white' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <ArrowLeft className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Back to issues</span><span className="sm:hidden">Back</span>
            </button>

            {/* Mobile Journey Stage Button */}
            <button
              onClick={() => setIsJourneyOpen(true)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-bold md:hidden border shrink-0 transition-all ${
                isDark 
                  ? 'bg-[#09151D] border-slate-700 text-[#34D399] hover:bg-[#0E202B]' 
                  : 'bg-teal-50 border-teal-200 text-teal-800 hover:bg-teal-100 shadow-sm'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              <span>{STAGE_LABELS[activeStep] || 'Stages'}</span>
            </button>

            {prevStepMap[activeStep] && (
              <button
                onClick={() => handleStepSelect(prevStepMap[activeStep])}
                className={`hidden md:inline-flex text-xs font-medium transition-colors ${
                  isDark ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-700'
                }`}
              >
                ← Prev Stage
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <span className={`text-xs font-mono font-medium hidden md:inline truncate max-w-[200px] lg:max-w-none ${
              isDark ? 'text-slate-400' : 'text-slate-500'
            }`}>
              {issue.repo_full_name} #{issue.github_issue_number}
            </span>
            
            <a
              href={issue.github_url || `https://github.com/${issue.repo_full_name}/issues/${issue.github_issue_number}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-lg transition-colors border ${
                isDark 
                  ? 'text-[#34D399] bg-[#071F1B] border-emerald-500/30 hover:bg-[#0E2C26]' 
                  : 'text-emerald-700 bg-emerald-50 border-emerald-200 hover:bg-emerald-100'
              }`}
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>

            <button
              onClick={toggleTheme}
              className={`p-1.5 rounded-xl border transition-all ${
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

        {/* Tab Sub-Views for the 10 Journey Stages */}
        <div className="flex-1 p-4 sm:p-8 pb-24 sm:pb-16">
          {activeStep === 'understand' && (
            <IssueOverviewView
              issue={issue}
              onExploreCode={() => handleStepSelect(nextStepMap['understand'])}
            />
          )}

          {activeStep === 'check_status' && (
            <ContributionStatusView
              issue={issue}
              onNextStage={() => handleStepSelect(nextStepMap['check_status'])}
            />
          )}

          {activeStep === 'learn' && (
            <LearnConceptsView
              issue={issue}
              onNextStage={() => handleStepSelect(nextStepMap['learn'])}
            />
          )}

          {activeStep === 'explore' && (
            <CodeExplorerView
              codeData={codeData}
              onBack={() => handleStepSelect('learn')}
              onCreatePlan={() => handleStepSelect(nextStepMap['explore'])}
            />
          )}

          {activeStep === 'investigate' && (
            <InvestigateView
              issue={issue}
              onNextStage={() => handleStepSelect(nextStepMap['investigate'])}
            />
          )}

          {activeStep === 'plan' && (
            <ContributionPlanView
              issue={issue}
              onProceedToCheckpoints={() => handleStepSelect(nextStepMap['plan'])}
            />
          )}

          {activeStep === 'implement' && (
            <ImplementGuideView
              issue={issue}
              onNextStage={() => handleStepSelect(nextStepMap['implement'])}
            />
          )}

          {activeStep === 'test' && (
            <TestGuideView
              issue={issue}
              onNextStage={() => handleStepSelect(nextStepMap['test'])}
            />
          )}

          {activeStep === 'prepare_pr' && (
            <PreparePRView
              issue={issue}
              onNextStage={() => handleStepSelect(nextStepMap['prepare_pr'])}
            />
          )}

          {activeStep === 'review' && (
            <ReviewChecklistView
              issue={issue}
            />
          )}
        </div>

        {/* Mobile Sticky Bottom Stage Navigation Bar */}
        <div className={`md:hidden fixed bottom-0 inset-x-0 p-3 border-t z-30 flex items-center justify-between gap-3 backdrop-blur-lg ${
          isDark ? 'bg-[#050B0E]/95 border-slate-800' : 'bg-white/95 border-slate-200 shadow-lg'
        }`}>
          {prevStepMap[activeStep] ? (
            <button
              onClick={() => handleStepSelect(prevStepMap[activeStep])}
              className={`inline-flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-bold border transition-colors ${
                isDark 
                  ? 'bg-[#09151D] border-slate-700 text-slate-300' 
                  : 'bg-slate-50 border-slate-200 text-slate-700'
              }`}
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Prev</span>
            </button>
          ) : (
            <div />
          )}

          <button
            onClick={() => setIsJourneyOpen(true)}
            className="text-[11px] font-mono font-bold text-[#34D399] px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30"
          >
            {STAGE_LABELS[activeStep] || activeStep}
          </button>

          {nextStepMap[activeStep] ? (
            <button
              onClick={() => handleStepSelect(nextStepMap[activeStep])}
              className="inline-flex items-center gap-1 px-4 py-2 bg-[#9FE8C3] hover:bg-[#86EFAC] text-[#064E3B] rounded-xl text-xs font-extrabold transition-all shadow-sm"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              onClick={() => navigate('/issues')}
              className="inline-flex items-center gap-1 px-3 py-2 bg-[#9FE8C3] text-[#064E3B] rounded-xl text-xs font-extrabold"
            >
              <span>Done</span>
            </button>
          )}
        </div>
      </main>
    </div>
  );
};

export default IssueWorkspacePage;
