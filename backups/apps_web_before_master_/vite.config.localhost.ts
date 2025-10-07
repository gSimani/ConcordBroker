import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Localhost-specific Vite configuration
export default defineConfig({
  plugins: [react()],

  // Development server configuration
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: false,

    // Proxy API calls to local backend services
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/mcp': {
        target: 'http://localhost:3005',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/mcp/, '')
      },
      '/supabase': {
        target: 'http://localhost:54321',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/supabase/, '')
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
        changeOrigin: true,
      }
    }
  },

  // Build configuration for localhost
  build: {
    outDir: 'dist-localhost',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-tabs'],
          'chart-vendor': ['chart.js', 'react-chartjs-2'],
          'supabase': ['@supabase/supabase-js'],
        }
      }
    }
  },

  // Path resolution
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@utils': path.resolve(__dirname, './src/utils'),
    }
  },

  // Environment variables
  define: {
    'import.meta.env.VITE_ENV': JSON.stringify('localhost'),
    'import.meta.env.VITE_SUPABASE_URL': JSON.stringify('http://localhost:54321'),
    'import.meta.env.VITE_API_URL': JSON.stringify('http://localhost:8001'),
    'import.meta.env.VITE_MCP_URL': JSON.stringify('http://localhost:3005'),
  },

  // Optimizations
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@supabase/supabase-js',
      'chart.js',
      'axios'
    ]
  }
})