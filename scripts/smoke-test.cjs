#!/usr/bin/env node
/**
 * ConcordBroker Smoke Test (CommonJS)
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

const MCP_URL = process.env.MCP_URL || 'http://localhost:3001';
const LANGCHAIN_URL = process.env.LANGCHAIN_URL || 'http://localhost:8003';
const MCP_API_KEY = process.env.MCP_API_KEY || 'concordbroker-mcp-key';

function argVal(flag, def) {
  const idx = process.argv.indexOf(flag);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return def;
}

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function checkMCP() {
  process.stdout.write('Checking MCP health... ');
  try {
    const { data } = await axios.get(`${MCP_URL}/health`);
    console.log('OK');
    return data;
  } catch (e) {
    console.log('FAILED');
    console.log('- Start MCP: cd mcp-server && npm start');
    throw e;
  }
}

async function checkLangChainWithRetry(retries = 6, delayMs = 3000) {
  for (let i = 0; i < retries; i++) {
    process.stdout.write(`Checking LangChain API (try ${i + 1}/${retries})... `);
    try {
      const { data } = await axios.get(`${LANGCHAIN_URL}/health`);
      console.log('OK');
      return data;
    } catch (e) {
      console.log('not ready');
      await wait(delayMs);
    }
  }
  throw new Error('LangChain API did not become healthy in time');
}

async function createRAGPipeline(documentPath, pipelineName) {
  process.stdout.write(`Creating RAG pipeline '${pipelineName}' from ${documentPath}... `);
  const abs = path.resolve(documentPath);
  if (!fs.existsSync(abs)) {
    console.log('SKIPPED (file not found)');
    return { skipped: true, reason: 'file not found' };
  }
  try {
    const { data } = await axios.post(`${LANGCHAIN_URL}/rag/create`, {
      document_path: abs,
      pipeline_name: pipelineName,
      chunk_size: 1000,
      chunk_overlap: 200,
    });
    console.log('OK');
    return data;
  } catch (e) {
    console.log('FAILED');
    return { error: e.message };
  }
}

async function chatTest() {
  process.stdout.write('Running agent chat (property_analysis)... ');
  try {
    const { data } = await axios.post(`${LANGCHAIN_URL}/chat`, {
      session_id: 'smoke_session',
      message: 'Hello! Provide a one-line confirmation reply.',
      agent_type: 'property_analysis',
      history: [],
      context: {},
    });
    console.log('OK');
    return data;
  } catch (e) {
    console.log('FAILED');
    return { error: e.message };
  }
}

async function main() {
  const ragPath = argVal('--rag', 'CLAUDE.md');
  const pipelineName = argVal('--pipeline', 'smoke_test');

  await checkMCP();
  await checkLangChainWithRetry();

  const rag = await createRAGPipeline(ragPath, pipelineName);
  const chat = await chatTest();

  console.log('\n=== Smoke Test Summary ===');
  console.log('MCP: healthy');
  console.log('LangChain: healthy');
  console.log('RAG:', rag?.status ? rag : rag?.error ? `error: ${rag.error}` : rag);
  if (chat?.response) {
    const meta = chat.metadata || {};
    console.log('Chat: ok');
    if (typeof meta.confidence !== 'undefined') {
      console.log(`  confidence: ${meta.confidence}`);
      console.log(`  escalated: ${meta.escalated}`);
      if (process.env.STRICT_ESCALATION === 'true' && meta.escalated) {
        console.log('  strict escalation active: response replaced with human-review notice');
      }
    }
  } else {
    console.log('Chat:', chat?.error ? `error: ${chat.error}` : chat);
  }
}

main().catch(err => {
  console.error('\nSmoke test failed:', err.message);
  process.exit(1);
});

