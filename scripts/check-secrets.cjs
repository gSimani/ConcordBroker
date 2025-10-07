#!/usr/bin/env node
// Simple secret pattern scan for hardcoded tokens and URLs
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const IGNORE_DIRS = new Set(['.git', 'node_modules', 'apps/web/dist', '.vercel', 'backups']);
const IGNORE_FILES = new Set(['.env', '.env.mcp']);

// Common token/url patterns to flag
const PATTERNS = [
  /https:\/\/[a-z0-9_-]{20,}\.supabase\.co/,
  /eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9/, // JWT-ish
  /ghp_[A-Za-z0-9]{20,}/,                 // GitHub PAT
  /github_pat_[A-Za-z0-9_\-]{20,}/,       // GitHub fine-grained
  /sk-ant-[A-Za-z0-9_\-]{10,}/,           // Anthropic
  /hf_[A-Za-z0-9]{10,}/,                   // HuggingFace
  /fc-[A-Za-z0-9]{10,}/,                   // Firecrawl
  /e2b_[A-Za-z0-9]{10,}/,                  // E2B
  /redis/i,
];

function shouldSkip(filePath) {
  const rel = path.relative(ROOT, filePath);
  if (!rel) return false;
  const parts = rel.split(path.sep);
  for (const p of parts) {
    if (IGNORE_DIRS.has(p)) return true;
  }
  const base = path.basename(rel);
  if (IGNORE_FILES.has(base)) return true;
  // Skip images/binaries
  if (/\.(png|jpg|jpeg|gif|ico|pdf|zip|tar|gz|mp4|map)$/i.test(base)) return true;
  return false;
}

function scanFile(filePath, findings) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    PATTERNS.forEach((re) => {
      if (re.test(content)) {
        findings.push({ file: filePath, pattern: re.toString() });
      }
    });
  } catch (_) {}
}

function walk(dir, findings) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (shouldSkip(p)) continue;
    if (e.isDirectory()) {
      walk(p, findings);
    } else if (e.isFile()) {
      scanFile(p, findings);
    }
  }
}

function main() {
  const findings = [];
  walk(ROOT, findings);
  if (!findings.length) {
    console.log('No hardcoded secrets detected (excluding env, dist, vercel, backups).');
    process.exit(0);
  }
  console.log('Potential hardcoded secrets found:');
  findings.slice(0, 200).forEach((f) => {
    console.log(`- ${path.relative(ROOT, f.file)} :: ${f.pattern}`);
  });
  process.exit(1);
}

if (require.main === module) main();

