import { createClient } from '@supabase/supabase-js'

// Localhost Supabase configuration
// Using Supabase local development server
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:54321'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

// Create Supabase client for localhost
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  },
  db: {
    schema: 'public'
  },
  global: {
    headers: {
      'x-client': 'concordbroker-localhost'
    }
  }
})

// Helper function to check connection
export async function checkSupabaseConnection() {
  try {
    const { data, error } = await supabase
      .from('florida_parcels')
      .select('count')
      .limit(1)
      .single()

    if (error) {
      console.error('Supabase connection error:', error)
      return false
    }

    console.log('Supabase connected successfully')
    return true
  } catch (err) {
    console.error('Failed to connect to Supabase:', err)
    return false
  }
}

// Helper to get localhost database URL
export function getLocalhostDatabaseUrl() {
  // For direct PostgreSQL connection
  return 'postgresql://postgres:postgres@localhost:54322/postgres'
}

// Helper to switch between local and remote
export function getSupabaseConfig() {
  const isLocalhost = window.location.hostname === 'localhost' ||
                     window.location.hostname === '127.0.0.1'

  if (isLocalhost) {
    return {
      url: 'http://localhost:54321',
      anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0',
      environment: 'localhost'
    }
  }

  // Production config (if needed)
  return {
    url: import.meta.env.VITE_SUPABASE_URL,
    anonKey: import.meta.env.VITE_SUPABASE_ANON_KEY,
    environment: 'production'
  }
}

export default supabase