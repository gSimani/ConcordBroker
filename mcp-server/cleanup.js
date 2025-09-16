/**
 * MCP Server Cleanup Script
 * Gracefully shuts down the MCP server and cleans up resources
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

async function cleanup() {
  console.log('🧹 Starting MCP Server cleanup...');
  
  const sessionFile = path.join(__dirname, '..', '.claude-session');
  const logFile = path.join(__dirname, 'claude-init.log');
  
  try {
    // Try to gracefully shut down the server
    console.log('Sending shutdown signal to MCP Server...');
    await axios.post('http://localhost:3001/shutdown', {}, { timeout: 2000 });
    console.log('✅ MCP Server shutdown signal sent');
  } catch (error) {
    console.log('⚠️ Could not send shutdown signal (server may already be stopped)');
  }
  
  // Clean up session file
  if (fs.existsSync(sessionFile)) {
    fs.unlinkSync(sessionFile);
    console.log('✅ Session file removed');
  }
  
  // Archive log file if it exists
  if (fs.existsSync(logFile)) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const archiveFile = path.join(__dirname, `logs`, `claude-init-${timestamp}.log`);
    
    // Create logs directory if it doesn't exist
    const logsDir = path.join(__dirname, 'logs');
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }
    
    // Move log file to archive
    fs.renameSync(logFile, archiveFile);
    console.log(`✅ Log file archived to ${archiveFile}`);
  }
  
  console.log('✅ Cleanup complete');
}

// Run cleanup
cleanup().catch(error => {
  console.error('Cleanup error:', error);
});