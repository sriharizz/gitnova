import { createClient } from '@supabase/supabase-js';

// Load variables safely for Vite
// Note: In Vercel, you must add these to "Settings > Environment Variables"
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY;

// Deployment Safety Check
let supabase = null;

if (!supabaseUrl || !supabaseKey) {
    console.error(
        "🚨 GitNova Error: Supabase environment variables are missing. \n" +
        "Check your Vercel Settings > Environment Variables. \n" +
        "Required: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY (or VITE_SUPABASE_KEY)."
    );
} else {
    supabase = createClient(supabaseUrl, supabaseKey);
}

export { supabase };