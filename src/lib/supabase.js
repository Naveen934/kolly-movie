import { createClient } from '@supabase/supabase-js';

// Derived from the connection string or given directly:
// URL: 'https://uuvkjqcnkgwhagpyfguz.supabase.co' (Wait, pooler URL is aws-1-ap-northeast-1.pooler.supabase.com, and user gave ID uuvkjqcnkgwhagpyfguz)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://uuvkjqcnkgwhagpyfguz.supabase.co';
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1dmtqcWNua2d3aGFncHlmZ3V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5NzYzNTAsImV4cCI6MjA4OTU1MjM1MH0.ew3GkB6uB6egtx5lWYDFdcEKaTtRDMHZYFEXNin6RBg';

export const supabase = createClient(supabaseUrl, supabaseKey);
