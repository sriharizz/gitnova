import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';

export const useIssues = (selectedCategory) => {
    const [issues, setIssues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Category Mapping Logic
    // Maps Frontend Reference -> Database Value
    const getDatabaseCategory = (frontendCategory) => {
        const map = {
            'AI': 'Machine Learning',
            'Web': 'Frontend',
            'Systems': 'DevOps',
            'Tools': 'Data Science', // Legacy ID fix
            'libraries': 'Data Science'
        };
        return map[frontendCategory] || frontendCategory;
    };

    const fetchIssues = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            let query = supabase
                .from('issues')
                .select('*')
                .eq('status', 'PUBLISHED');

            let mappedCategory = null;

            if (selectedCategory) {
                // Robust filtering: Handle both string and array inputs
                const rawCategory = Array.isArray(selectedCategory)
                    ? selectedCategory[0]
                    : selectedCategory;

                if (rawCategory) {
                    mappedCategory = getDatabaseCategory(rawCategory);
                    // Using eq() for exact match as requested in standard repair plan
                    // But if DB has mixed case or issues, strictly requested ".eq"
                    query = query.eq('category', mappedCategory);
                }
            }

            const { data, error: supabaseError } = await query;

            if (supabaseError) throw supabaseError;

            console.log(`[GitNova] Fetched for ${mappedCategory}:`, data?.length);

            if (!data || data.length === 0) {
                // FALLBACK: If specific category is empty, check if DB has ANY data (Debug)
                const { count } = await supabase.from('issues').select('*', { count: 'exact', head: true });
                console.log('[GitNova] Total DB Issues:', count);

                // Optional: You could fetch random issues here if you wanted to show *something*
                // setIssues(fallbackData); 
            }

            if (!data || data.length === 0) {
                console.warn(`[GitNova] Category ${mappedCategory} is empty. Activating Fallback Protocol.`);

                // FALLBACK: Fetch any 10 'PUBLISHED' issues to populate the UI
                const { data: fallbackData, error: fallbackError } = await supabase
                    .from('issues')
                    .select('*')
                    .eq('status', 'PUBLISHED')
                    .limit(10);

                if (fallbackData && fallbackData.length > 0) {
                    console.log('[GitNova] Fallback successful:', fallbackData.length);
                    setIssues(fallbackData);
                    return;
                }
            }

            setIssues(data || []);
        } catch (err) {
            console.error('Error fetching issues:', err);
            setError(err.message || 'Could not load recommendations');
        } finally {
            setLoading(false);
        }
    }, [selectedCategory]);

    useEffect(() => {
        fetchIssues();
    }, [fetchIssues]);

    return { issues, loading, error, refreshIssues: fetchIssues };
};
