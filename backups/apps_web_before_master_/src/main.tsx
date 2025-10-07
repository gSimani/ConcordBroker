import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import './styles/elegant-property.css'
import { registerSW } from './utils/serviceWorker'

console.log('main.tsx starting')

// Fix for React DevTools extension conflict
if (typeof window !== 'undefined') {
  // Ensure React DevTools hook is properly initialized
  if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
    console.log('React DevTools detected')
    // Sometimes the extension needs a small delay to properly initialize
    setTimeout(() => {
      console.log('Delayed render for DevTools compatibility')
    }, 0)
  }
}

const rootElement = document.getElementById('root')
if (!rootElement) {
  console.error('Root element not found!')
  document.body.innerHTML = '<h1>Error: Root element not found</h1>'
} else {
  console.log('Root element found, creating React app')

  // Use a small delay to ensure DevTools is ready
  const renderApp = () => {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
    )
    console.log('React app rendered')
  }

  // Register service worker for offline capabilities
  registerSW({
    onSuccess: () => {
      console.log('Service Worker: Successfully registered for offline use');
    },
    onUpdate: () => {
      console.log('Service Worker: New version available - please refresh');
    },
    onOfflineReady: () => {
      console.log('Service Worker: App ready for offline use');
    }
  });

  // Check if we need to wait for DevTools
  if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
    // Give DevTools a moment to initialize
    requestAnimationFrame(renderApp)
  } else {
    renderApp()
  }
}