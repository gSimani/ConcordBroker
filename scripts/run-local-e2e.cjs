#!/usr/bin/env node
/**
 * Run local end-to-end verification:
 * - Start MCP (if not healthy)
 * - Start LangChain API (if not healthy)
 * - Run verify and smoke
 * - Cleanup started processes
 */

const { spawn } = require('child_process');
const axios = require('axios');

const MCP_URL = process.env.MCP_URL || 'http://127.0.0.1:3001';
const LANGCHAIN_URL = process.env.LANGCHAIN_URL || 'http://127.0.0.1:8003';
const ONLINE = process.env.E2E_ONLINE === 'true';

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function waitForHealth(url, tries = 20, delay = 1000) {
  for (let i = 0; i < tries; i++) {
    try {
      const { status } = await axios.get(`${url}/health`, { timeout: 1000 });
      if (status === 200) return true;
    } catch {}
    await wait(delay);
  }
  return false;
}

function startMCP() {
  return spawn(process.execPath.replace('node.exe','node').replace('node','node'), ['server.js'], {
    cwd: 'mcp-server',
    stdio: ['ignore','inherit','inherit']
  });
}

function startLangChain(pyCmd) {
  const args = ['-m','uvicorn','apps.api.langchain_api:app','--host','127.0.0.1','--port','8003'];
  const env = { ...process.env };
  if (!ONLINE) env.OFFLINE_MODE = 'true';
  return spawn(pyCmd, args, { stdio: ['ignore','inherit','inherit'], env });
}

async function findPython() {
  // Try common commands
  const candidates = ['python', 'py', 'python3'];
  for (const cmd of candidates) {
    try {
      await new Promise((resolve, reject) => {
        const p = spawn(cmd, ['--version']);
        p.on('error', reject);
        p.on('exit', (code) => code === 0 ? resolve() : reject());
      });
      return cmd;
    } catch {}
  }
  return null;
}

async function runNode(script) {
  return new Promise((resolve) => {
    const p = spawn(process.execPath, [script], { stdio: 'inherit' });
    p.on('exit', code => resolve(code === 0));
  });
}

(async () => {
  let mcpProc; let lcProc;
  try {
    // MCP
    process.stdout.write('Checking MCP... ');
    let mcpHealthy = await waitForHealth(MCP_URL, 2, 500);
    if (!mcpHealthy) {
      console.log('starting');
      mcpProc = startMCP();
      mcpHealthy = await waitForHealth(MCP_URL, 40, 500);
    } else {
      console.log('already healthy');
    }
    if (!mcpHealthy) throw new Error('MCP did not become healthy');

    // LangChain
    process.stdout.write('Checking LangChain... ');
    let lcHealthy = await waitForHealth(LANGCHAIN_URL, 2, 500);
    if (!lcHealthy) {
      const py = await findPython();
      if (!py) throw new Error('Python not found to start LangChain API');
      console.log('starting');
      lcProc = startLangChain(py);
      lcHealthy = await waitForHealth(LANGCHAIN_URL, 60, 500);
    } else {
      console.log('already healthy');
    }
    if (!lcHealthy) throw new Error('LangChain did not become healthy');

    // Verify
    console.log('Running verify...');
    const okVerify = await runNode('scripts/verify-completion.cjs');
    if (!okVerify) throw new Error('Verification failed');

    // Smoke
    console.log('\nRunning smoke...');
    const okSmoke = await runNode('scripts/smoke-test.cjs');
    if (!okSmoke) throw new Error('Smoke failed');

    console.log('\nE2E: PASSED');
  } catch (e) {
    console.error('\nE2E: FAILED -', e.message);
    process.exitCode = 1;
  } finally {
    if (lcProc) { try { lcProc.kill(); } catch {} }
    if (mcpProc) { try { mcpProc.kill(); } catch {} }
  }
})();
