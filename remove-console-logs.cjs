/**
 * Script to remove console.log statements from TypeScript/JavaScript files
 * Keeps console.error and console.warn for production debugging
 */

const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

const DRY_RUN = process.argv.includes('--dry-run');
const REMOVE_ALL = process.argv.includes('--all');

let filesProcessed = 0;
let linesRemoved = 0;

function removeConsoleLogs(content) {
  const lines = content.split('\n');
  const newLines = [];
  let removed = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Skip if it's a comment
    if (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*')) {
      newLines.push(line);
      continue;
    }

    // Patterns to remove
    const shouldRemove = REMOVE_ALL
      ? /console\.(log|debug|info|warn|error)/
      : /console\.(log|debug)/; // Keep error and warn by default

    if (trimmed.match(shouldRemove)) {
      // Check if it's a multi-line console statement
      if (trimmed.includes('console.') && !trimmed.includes(');')) {
        // Start of multi-line, skip until we find the closing
        let j = i + 1;
        while (j < lines.length && !lines[j].includes(');')) {
          j++;
        }
        i = j; // Skip to end of multi-line statement
        removed++;
        continue;
      }

      removed++;
      continue; // Skip this line
    }

    newLines.push(line);
  }

  return { content: newLines.join('\n'), removed };
}

async function processFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const { content: newContent, removed } = removeConsoleLogs(content);

    if (removed > 0) {
      console.log(`${filePath}: ${removed} console statements`);

      if (!DRY_RUN) {
        fs.writeFileSync(filePath, newContent, 'utf8');
      }

      filesProcessed++;
      linesRemoved += removed;
    }
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
  }
}

async function main() {
  console.log('🔍 Searching for console statements...\n');

  if (DRY_RUN) {
    console.log('🔵 DRY RUN MODE - No files will be modified\n');
  }

  if (REMOVE_ALL) {
    console.log('⚠️  REMOVE ALL MODE - Will remove console.error and console.warn too\n');
  } else {
    console.log('✓ Safe mode - Keeping console.error and console.warn\n');
  }

  const files = await glob('apps/web/src/**/*.{ts,tsx,js,jsx}', {
    ignore: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/*.test.*',
      '**/*.spec.*'
    ]
  });

  console.log(`Found ${files.length} files to process\n`);

  for (const file of files) {
    await processFile(file);
  }

  console.log(`\n✅ Complete!`);
  console.log(`Files processed: ${filesProcessed}`);
  console.log(`Console statements removed: ${linesRemoved}`);

  if (DRY_RUN) {
    console.log('\n💡 Run without --dry-run to actually remove console statements');
  }
}

main().catch(console.error);
