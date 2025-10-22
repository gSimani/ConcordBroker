#!/usr/bin/env node
/**
 * Hook Consolidation Script
 * Safely identifies and removes redundant hooks
 * Validates no active imports before deletion
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Hooks to KEEP (core functionality)
const KEEP_HOOKS = [
  'useAdvancedPropertySearch.ts',
  'useOptimizedPropertySearch.ts',
  'useSalesData.ts',
  'useSunbizMatching.ts',
  'useDebounce.ts', // Utility - used by others
  'useInfiniteScroll.ts' // UI utility - might be used
];

// Hooks to DELETE (redundant/deprecated)
const DELETE_HOOKS = [
  'useOptimizedPropertySearchV2.ts',
  'usePropertyData.ts',
  'usePropertyDataOptimized.ts',
  'usePropertyDataImproved.ts',
  'useCompletePropertyData.ts',
  'useComprehensivePropertyData.ts',
  'useSupabaseProperties.ts',
  'useOptimizedSupabase.ts',
  'useBatchSalesData.ts',
  'useJupyterPropertyData.ts',
  'usePySparkData.ts',
  'useSQLAlchemyData.ts',
  'usePropertyAppraiser.ts',
  'useTrackedData.ts',
  'useOwnerProperties.ts',
  'usePropertyAutocomplete.ts',
  'useOptimizedSearch.ts',
  'useSmartDebounce.ts'
];

const HOOKS_DIR = path.join(__dirname, '../apps/web/src/hooks');
const SRC_DIR = path.join(__dirname, '../apps/web/src');

console.log('🔧 Hook Consolidation Script\n');
console.log('=' .repeat(80));

// Step 1: Verify hooks directory exists
if (!fs.existsSync(HOOKS_DIR)) {
  console.error('❌ ERROR: Hooks directory not found:', HOOKS_DIR);
  process.exit(1);
}

// Step 2: List all existing hooks
console.log('\n📂 Scanning hooks directory...\n');
const allHooks = fs.readdirSync(HOOKS_DIR).filter(f => f.endsWith('.ts'));
console.log(`Found ${allHooks.length} hook files\n`);

// Step 3: Categorize hooks
const keepHooks = allHooks.filter(h => KEEP_HOOKS.includes(h));
const deleteHooks = allHooks.filter(h => DELETE_HOOKS.includes(h));
const unknownHooks = allHooks.filter(h => !KEEP_HOOKS.includes(h) && !DELETE_HOOKS.includes(h));

console.log('✅ Hooks to KEEP:', keepHooks.length);
keepHooks.forEach(h => console.log(`   - ${h}`));

console.log('\n❌ Hooks to DELETE:', deleteHooks.length);
deleteHooks.forEach(h => console.log(`   - ${h}`));

if (unknownHooks.length > 0) {
  console.log('\n⚠️  Unknown hooks (not in keep or delete list):', unknownHooks.length);
  unknownHooks.forEach(h => console.log(`   - ${h}`));
}

// Step 4: Check for active imports
console.log('\n' + '='.repeat(80));
console.log('\n🔍 Checking for active imports...\n');

const results = {
  safe: [],
  unsafe: [],
  errors: []
};

for (const hookFile of deleteHooks) {
  const hookName = hookFile.replace('.ts', '');

  try {
    // Search for imports in src directory
    const grepCommand = `grep -r "import.*${hookName}" "${SRC_DIR}" --include="*.ts" --include="*.tsx" 2>/dev/null || true`;
    const output = execSync(grepCommand, { encoding: 'utf-8' });

    if (output.trim()) {
      // Found imports
      const lines = output.trim().split('\n');
      console.log(`❌ ${hookName} - FOUND ${lines.length} import(s):`);
      lines.forEach(line => console.log(`   ${line}`));
      results.unsafe.push({ hook: hookName, imports: lines });
    } else {
      // No imports found - safe to delete
      console.log(`✅ ${hookName} - No imports found (SAFE TO DELETE)`);
      results.safe.push(hookName);
    }
  } catch (err) {
    console.log(`⚠️  ${hookName} - Error checking: ${err.message}`);
    results.errors.push({ hook: hookName, error: err.message });
  }
}

// Step 5: Summary and recommendations
console.log('\n' + '='.repeat(80));
console.log('\n📊 SUMMARY:\n');
console.log(`✅ Safe to delete:     ${results.safe.length} hooks`);
console.log(`❌ Has active imports: ${results.unsafe.length} hooks`);
console.log(`⚠️  Errors:            ${results.errors.length} hooks`);

if (results.safe.length > 0) {
  console.log('\n🗑️  SAFE TO DELETE:\n');
  results.safe.forEach(hook => {
    console.log(`   rm apps/web/src/hooks/${hook}.ts`);
  });
}

if (results.unsafe.length > 0) {
  console.log('\n⚠️  CANNOT DELETE (has imports):\n');
  results.unsafe.forEach(({ hook, imports }) => {
    console.log(`   ${hook} - ${imports.length} import(s) found`);
    console.log(`   Action required: Migrate to recommended hook first\n`);
  });
}

// Step 6: Generate deletion script
if (results.safe.length > 0) {
  const deleteScriptPath = path.join(__dirname, 'delete-redundant-hooks.sh');
  const deleteScript = [
    '#!/bin/bash',
    '# Auto-generated hook deletion script',
    '# Run this to delete redundant hooks that have no active imports\n',
    'cd "$(dirname "$0")/.."',
    'echo "🗑️  Deleting redundant hooks..."\n'
  ];

  results.safe.forEach(hook => {
    deleteScript.push(`echo "Deleting ${hook}..."`);
    deleteScript.push(`rm -f apps/web/src/hooks/${hook}.ts`);
  });

  deleteScript.push('\necho "✅ Deleted ${' + results.safe.length + '} redundant hooks"');
  deleteScript.push('echo "Run: git status"');

  fs.writeFileSync(deleteScriptPath, deleteScript.join('\n'), { mode: 0o755 });
  console.log(`\n✅ Created deletion script: ${deleteScriptPath}`);
  console.log('\nTo delete safe hooks, run:');
  console.log(`   bash ${deleteScriptPath}`);
}

// Step 7: Generate migration guide for unsafe hooks
if (results.unsafe.length > 0) {
  const migrationGuidePath = path.join(__dirname, '../HOOK_MIGRATION_GUIDE.md');
  const guide = [
    '# Hook Migration Guide\n',
    '## Hooks That Need Migration\n',
    'The following hooks have active imports and need to be migrated before deletion:\n'
  ];

  results.unsafe.forEach(({ hook, imports }) => {
    guide.push(`### ${hook}\n`);
    guide.push(`**Found ${imports.length} import(s):**\n`);
    guide.push('```');
    imports.forEach(imp => guide.push(imp));
    guide.push('```\n');

    // Add recommended replacement
    const recommendations = {
      'useOptimizedPropertySearchV2': 'useAdvancedPropertySearch',
      'usePropertyDataOptimized': 'useAdvancedPropertySearch',
      'useCompletePropertyData': 'useAdvancedPropertySearch',
      'useComprehensivePropertyData': 'useAdvancedPropertySearch',
      'useBatchSalesData': 'useSalesData'
    };

    const recommended = recommendations[hook] || 'useAdvancedPropertySearch (for property searches) or useSalesData (for sales data)';
    guide.push(`**Recommended replacement:** \`${recommended}\`\n`);
    guide.push('**Migration steps:**');
    guide.push('1. Open each file listed above');
    guide.push(`2. Replace \`import { ${hook} } from ...\` with \`import { ${recommended} } from ...\``);
    guide.push(`3. Update hook usage to match ${recommended} API`);
    guide.push('4. Test component still works');
    guide.push(`5. Delete ${hook}.ts\n`);
    guide.push('---\n');
  });

  fs.writeFileSync(migrationGuidePath, guide.join('\n'));
  console.log(`\n📝 Created migration guide: ${migrationGuidePath}`);
}

// Step 8: Exit with appropriate code
console.log('\n' + '='.repeat(80));

if (results.unsafe.length === 0 && results.safe.length > 0) {
  console.log('\n✅ ALL REDUNDANT HOOKS CAN BE SAFELY DELETED');
  console.log('\nRun the deletion script when ready:');
  console.log(`   bash scripts/delete-redundant-hooks.sh\n`);
  process.exit(0);
} else if (results.unsafe.length > 0) {
  console.log('\n⚠️  SOME HOOKS HAVE ACTIVE IMPORTS');
  console.log('\nRead migration guide:');
  console.log(`   HOOK_MIGRATION_GUIDE.md`);
  console.log('\nAfter migration, run this script again.\n');
  process.exit(1);
} else {
  console.log('\n✅ NO REDUNDANT HOOKS TO DELETE\n');
  process.exit(0);
}
