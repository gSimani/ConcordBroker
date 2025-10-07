const fs = require('fs');
const path = require('path');

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function moveIfExists(src, destDir) {
  if (fs.existsSync(src)) {
    const base = path.basename(src);
    const dest = path.join(destDir, base);
    fs.renameSync(src, dest);
    return dest;
  }
  return null;
}

function main() {
  const repoRoot = process.cwd();
  const backupDir = path.join(repoRoot, 'backups', 'strays');
  ensureDir(backupDir);
  const moved = [];

  // apps/web/nul
  const nulPath = path.join(repoRoot, 'apps', 'web', 'nul');
  const res1 = moveIfExists(nulPath, backupDir);
  if (res1) moved.push(res1);

  // Files at repo root starting with 'C:Users'
  const entries = fs.readdirSync(repoRoot);
  for (const name of entries) {
    if (name.startsWith('C:Users')) {
      const res = moveIfExists(path.join(repoRoot, name), backupDir);
      if (res) moved.push(res);
    }
  }

  if (moved.length) {
    console.log('Quarantined stray files to', backupDir);
    for (const m of moved) console.log(' -', m);
  } else {
    console.log('No stray files found to quarantine.');
  }
}

if (require.main === module) {
  try {
    main();
  } catch (e) {
    console.error('Error:', e.message);
    process.exit(1);
  }
}

