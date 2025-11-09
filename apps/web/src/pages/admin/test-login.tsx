import React, { useState } from 'react';
import { supabase } from '@/lib/supabase';

export default function TestLogin() {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<any>(null);

  const testQuery = async () => {
    const url = import.meta.env.VITE_SUPABASE_URL;
    const key = import.meta.env.VITE_SUPABASE_ANON_KEY;

    console.log('Testing Supabase connection...');
    console.log('Supabase URL:', url);
    console.log('Supabase Key (first 20 chars):', key?.substring(0, 20));
    console.log('Has URL:', !!url);
    console.log('Has Key:', !!key);

    try {
      const { data, error } = await supabase
        .from('admin_users')
        .select('*')
        .eq('email', 'admin@concordbroker.com')
        .eq('status', 'active')
        .limit(1);

      console.log('Query result:', { data, error });

      if (error) {
        setError(error);
        console.error('Error:', error);
      } else {
        setResult(data);
        console.log('Success:', data);
      }
    } catch (err) {
      console.error('Exception:', err);
      setError(err);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Supabase Login Test</h1>

      <button
        onClick={testQuery}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          cursor: 'pointer',
          marginBottom: '20px'
        }}
      >
        Test Query
      </button>

      {error && (
        <div style={{
          padding: '20px',
          background: '#fee',
          border: '1px solid #fcc',
          marginBottom: '20px'
        }}>
          <h3>Error:</h3>
          <pre>{JSON.stringify(error, null, 2)}</pre>
        </div>
      )}

      {result && (
        <div style={{
          padding: '20px',
          background: '#efe',
          border: '1px solid #cfc'
        }}>
          <h3>Result:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
          <p><strong>Found {result.length} user(s)</strong></p>
        </div>
      )}

      <div style={{ marginTop: '20px', padding: '20px', background: '#f5f5f5' }}>
        <h3>Expected User:</h3>
        <pre>Email: admin@concordbroker.com
Status: active
Role: super_admin</pre>
      </div>
    </div>
  );
}
