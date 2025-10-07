/**
 * Simple HTTP server for DOR County Dashboard
 * Serves the dashboard with proper CORS headers
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;
const DASHBOARD_FILE = path.join(__dirname, 'county_progress_dashboard.html');
const PROGRESS_FILE = path.join(__dirname, 'progress_tracker.json');

const server = http.createServer((req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Serve the dashboard
  if (req.url === '/' || req.url === '/index.html') {
    fs.readFile(DASHBOARD_FILE, 'utf8', (err, data) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Error loading dashboard');
        return;
      }

      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(data);
    });
  } else if (req.url.startsWith('/progress_tracker.json')) {
    fs.readFile(PROGRESS_FILE, 'utf8', (err, data) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Error loading progress');
        return;
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(data);
    });
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

server.listen(PORT, () => {
  console.log('='.repeat(80));
  console.log('DOR COUNTY DASHBOARD SERVER');
  console.log('='.repeat(80));
  console.log(`Server running at: http://localhost:${PORT}`);
  console.log(`Dashboard file: ${DASHBOARD_FILE}`);
  console.log('');
  console.log('Dashboard features:');
  console.log('  - Real-time county progress monitoring');
  console.log('  - Live activity log');
  console.log('  - ETA calculations');
  console.log('  - Processing speed metrics');
  console.log('  - Auto-refresh every 10 seconds');
  console.log('');
  console.log('Press Ctrl+C to stop the server');
  console.log('='.repeat(80));
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\nShutting down dashboard server...');
  server.close(() => {
    console.log('Server stopped');
    process.exit(0);
  });
});
