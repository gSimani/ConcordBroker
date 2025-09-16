/**
 * Guardrail quick checks (no test framework required)
 * - Validates redact_pii masks emails and phone numbers
 *
 * Usage:
 *   node scripts/guardrail-check.js
 */

const { spawnSync } = require('child_process');

function pyEval(code) {
  // Try python3, then python
  const tryCmd = (cmd) => spawnSync(cmd, ['- <<PY\n' + code + '\nPY'], { shell: true });
  let r = tryCmd('python3');
  if (r.error || r.status !== 0) {
    r = tryCmd('python');
  }
  if (r.error) throw r.error;
  return { stdout: r.stdout?.toString() || '', stderr: r.stderr?.toString() || '' };
}

const py = `
from apps.langchain_system.util_guardrails import redact_pii

samples = [
    ("Contact me at alice@example.com for details", "email"),
    ("My phone is 305-555-1234, call me.", "phone"),
    ("Multi: bob.smith@corp.co and (561) 222-3344", "both"),
]

for s, t in samples:
    masked = redact_pii(s)
    print(t, '=>', masked)
`;

try {
  const { stdout, stderr } = pyEval(py);
  if (stderr) throw new Error(stderr);
  console.log(stdout.trim());
  console.log('\nGuardrail check completed.');
} catch (e) {
  console.error('Guardrail check failed:', e.message);
  process.exit(1);
}
