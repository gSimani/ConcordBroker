import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

function SimpleHome() {
  return (
    <div style={{ padding: '20px', backgroundColor: 'white', minHeight: '100vh' }}>
      <h1>ConcordBroker - Debug Version</h1>
      <p>If you can see this, React is working without lazy loading!</p>
      <div style={{ marginTop: '20px' }}>
        <h2>Test Components:</h2>
        <div style={{ padding: '10px', border: '1px solid #ccc', margin: '10px 0' }}>
          <h3>Navigation Test</h3>
          <a href="/dashboard" style={{ marginRight: '10px' }}>Dashboard</a>
          <a href="/properties" style={{ marginRight: '10px' }}>Properties</a>
        </div>
        <div style={{ padding: '10px', border: '1px solid #ccc', margin: '10px 0' }}>
          <h3>Styling Test</h3>
          <button style={{ padding: '10px 20px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '5px' }}>
            Test Button
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  console.log('Debug App is rendering');

  return (
    <Router>
      <Routes>
        <Route path="/" element={<SimpleHome />} />
        <Route path="*" element={<div style={{ padding: '20px' }}>404 - Page not found</div>} />
      </Routes>
    </Router>
  )
}

export default App