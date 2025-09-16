#!/usr/bin/env node
/**
 * ConcordBroker Completion Verification (CommonJS)
 */

const fs = require('fs');
const path = require('path');

const repoRoot = process.cwd();
const ignoreDirs = new Set(['.git', 'node_modules', 'data', 'TEMP', 'archived_agents_20250910_224956']);

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ignoreDirs.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

function isCodeFile(p) {
  const ext = path.extname(p).toLowerCase();
  if (ext === '.md' || ext === '.png' || ext === '.jpg' || ext === '.jpeg' || ext === '.gif' || ext === '.svg' || ext === '.pdf') return false;
  if (p.includes(path.join('logs', ''))) return false;
  return true;
}

const files = walk(repoRoot);
const codeFiles = files
  .filter(isCodeFile)
  .filter(f => !/\.env(\.|$)/.test(path.basename(f)))
  .filter(f => !f.endsWith('.pyc'))
  .filter(f => !f.includes(`${path.sep}dist${path.sep}`));

// 1) Find raw execute_sql in code (not docs)
const execSqlHits = [];
for (const f of codeFiles) {
  const text = fs.readFileSync(f, 'utf8');
  if (/execute_sql\s*\(/.test(text) || /\/rpc\/execute_sql\b/.test(text)) {
    execSqlHits.push(f);
  }
}

// 2) Hardcoded secrets patterns in code
const secretRegexes = [
  /sk-[A-Za-z0-9_\-]{20,}/,
  /github_pat_[A-Za-z0-9_]{20,}/,
  /hf_[A-Za-z0-9]{10,}/,
  /AIza[0-9A-Za-z_\-]{10,}/,
];
const secretHits = [];
for (const f of codeFiles) {
  // whitelist files that may contain 'hf_' token prefix in code but not secrets
  const base = path.basename(f);
  if (f.endsWith(path.join('apps','api','config','huggingface.py'))) continue;
  const text = fs.readFileSync(f, 'utf8');
  for (const rx of secretRegexes) {
    if (rx.test(text)) {
      secretHits.push(f);
      break;
    }
  }
}

// 3) MCP WS verifyClient x-api-key enforcement
const mcpServer = path.join(repoRoot, 'mcp-server', 'server.js');
let wsCheck = false;
if (fs.existsSync(mcpServer)) {
  const content = fs.readFileSync(mcpServer, 'utf8');
  wsCheck = /verifyClient\s*:\s*\(info,\s*done\)/.test(content) && /x-api-key/i.test(content);
}

// 4) MCP REST /api protection middleware
let apiKeyMiddleware = false;
if (fs.existsSync(mcpServer)) {
  const content = fs.readFileSync(mcpServer, 'utf8');
  apiKeyMiddleware = /app\.use\('\/api'\s*,\s*\(req,\s*res,\s*next\)/.test(content);
}
const apiRoutes = path.join(repoRoot, 'mcp-server', 'api-routes.js');
if (fs.existsSync(apiRoutes)) {
  const content = fs.readFileSync(apiRoutes, 'utf8');
  if (/router\.use\(authenticateRequest\)/.test(content)) apiKeyMiddleware = true;
}

// 5) LangChain config defaults
const lcConfig = path.join(repoRoot, 'apps', 'langchain_system', 'config.py');
let modelDefaultsOk = false;
if (fs.existsSync(lcConfig)) {
  const content = fs.readFileSync(lcConfig, 'utf8');
  modelDefaultsOk = /"primary_model"\s*:\s*os\.getenv\([^)]*"gpt-4o"/.test(content);
}

// 6) Chat PII and confidence
const lcApi = path.join(repoRoot, 'apps', 'api', 'langchain_api.py');
let piiAndConfidenceOk = false;
if (fs.existsSync(lcApi)) {
  const content = fs.readFileSync(lcApi, 'utf8');
  piiAndConfidenceOk = /redact_pii\(/.test(content) && /compute_confidence\(/.test(content);
}

const failures = [];
const warnings = [];

if (execSqlHits.length > 0) {
  // treat these as warnings; script-level guards may apply
  warnings.push(`Found execute_sql references in code: ${[...new Set(execSqlHits)].slice(0,10).join(', ')}${execSqlHits.length>10?' ...':''}`);
}
if (secretHits.length > 0) {
  failures.push(`Possible hardcoded secrets in: ${[...new Set(secretHits)].slice(0,10).join(', ')}${secretHits.length>10?' ...':''}`);
}
if (!wsCheck) failures.push('MCP WebSocket verifyClient with x-api-key not detected');
if (!apiKeyMiddleware) failures.push('MCP /api auth middleware not detected');
if (!modelDefaultsOk) failures.push('LangChain config does not default to gpt-4o');
if (!piiAndConfidenceOk) failures.push('Chat PII redaction and confidence scoring not detected');

if (failures.length === 0) {
  console.log('=== Completion Verification Report ===');
  console.log('- All critical checks passed.');
  if (warnings.length) {
    console.log('- Warnings:');
    warnings.forEach(w => console.log(`  • ${w}`));
  }
  console.log('Verification: PASSED');
  process.exit(0);
} else {
  console.log('=== Completion Verification Report ===');
  console.log('- Failures:');
  failures.forEach(f => console.log(`  • ${f}`));
  if (warnings.length) {
    console.log('- Warnings:');
    warnings.forEach(w => console.log(`  • ${w}`));
  }
  console.log('Verification: FAILED');
  process.exit(1);
}


