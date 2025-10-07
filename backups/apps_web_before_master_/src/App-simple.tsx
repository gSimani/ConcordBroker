import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'

function SimpleHome() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>ConcordBroker - Home Page</h1>
      <p>If you can see this, React is working!</p>
    </div>
  )
}

function App() {
  console.log('Simple App is rendering');

  return (
    <Router>
      <Routes>
        <Route path="/" element={<SimpleHome />} />
        <Route path="*" element={<div>404 - Page not found</div>} />
      </Routes>
    </Router>
  )
}

export default App