import { createClient } from '@supabase/supabase-js';

// Load variables safely for Vite
// Note: In Vercel, you must add these to "Settings > Environment Variables"
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY; // Using your existing variable name

// Deployment Safety Check
let supabase = null;

if (!supabaseUrl || !supabaseKey) {
    console.error(
        "🚨 GitNova Error: Supabase environment variables are missing. \n" +
        "If you are on Vercel, go to Settings > Environment Variables and add VITE_SUPABASE_URL and VITE_SUPABASE_KEY."
    );
} else {
    supabase = createClient(supabaseUrl, supabaseKey);
}

export { supabase };