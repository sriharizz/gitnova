import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Get aggregate platform metrics for landing page stats.
 * Throws on failure — caller must handle the error.
 */
export const fetchStats = async () => {
  const res = await client.get('/stats');
  return res.data;
};

/**
 * Get personalized issue recommendations.
 * Throws on failure — caller must handle the error.
 */
export const fetchRecommendations = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.languages) query.append('languages', Array.isArray(params.languages) ? params.languages.join(',') : params.languages);
  if (params.domains) query.append('domains', Array.isArray(params.domains) ? params.domains.join(',') : params.domains);
  if (params.difficulty) query.append('difficulty', params.difficulty);
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);

  const res = await client.get(`/recommendations?${query.toString()}`);
  return res.data;
};

/**
 * Fetch issue feed with optional filters.
 * Throws on failure — caller must handle the error.
 */
export const fetchIssues = async (filters = {}) => {
  const query = new URLSearchParams();
  if (filters.difficulty_tier) query.append('difficulty_tier', filters.difficulty_tier);
  if (filters.language) query.append('language', filters.language);
  if (filters.domain) query.append('domain', filters.domain);
  if (filters.verification_status) query.append('verification_status', filters.verification_status);
  if (filters.limit) query.append('limit', filters.limit);
  if (filters.offset) query.append('offset', filters.offset);

  const res = await client.get(`/issues?${query.toString()}`);
  return res.data;
};

/**
 * Get a single issue by ID with its precomputed explanation.
 * Throws on failure — caller must handle the error.
 */
export const fetchIssueById = async (issueId) => {
  const res = await client.get(`/issues/${issueId}`);
  return res.data;
};

/**
 * Get retrieved code chunks for Code Explorer.
 * Throws on failure — caller must handle the error.
 */
export const fetchIssueCode = async (issueId) => {
  const res = await client.get(`/issues/${issueId}/code`);
  return res.data;
};

/**
 * Get the structured 10-stage Contribution Journey for a specific issue.
 * Throws on failure — caller must handle the error.
 */
export const fetchIssueJourney = async (issueId) => {
  const res = await client.get(`/issues/${issueId}/journey`);
  return res.data;
};

/**
 * Save user preferences to Supabase.
 */
export const saveUserPreferences = async (preferences) => {
  const payload = {
    user_id: preferences.user_id || 'default_user',
    preferred_languages: preferences.languages || preferences.preferred_languages || [],
    preferred_domains: preferences.domains || preferences.preferred_domains || [],
    preferred_difficulty: preferences.difficulty || preferences.preferred_difficulty || 'BEGINNER',
    preferred_contribution_types: preferences.contribution_types || []
  };
  const res = await client.post('/user/preferences', payload);
  return res.data;
};

/**
 * Fetch stored user preferences from Supabase.
 */
export const fetchUserPreferences = async (userId = 'default_user') => {
  const res = await client.get(`/user/preferences?user_id=${userId}`);
  return res.data;
};

