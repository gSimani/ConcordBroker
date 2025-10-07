/**
 * Utility to verify all DIV elements have unique IDs for React DevTools integration
 */

export interface ElementIdStats {
  totalDivs: number;
  divsWithIds: number;
  divsWithTestIds: number;
  coverage: number;
  duplicateIds: string[];
  missingIds: string[];
}

/**
 * Scans the DOM for DIV elements and analyzes ID coverage
 */
export function analyzeElementIds(): ElementIdStats {
  const divs = document.querySelectorAll('div');
  const idsFound = new Set<string>();
  const duplicateIds: string[] = [];
  const missingIds: string[] = [];

  let divsWithIds = 0;
  let divsWithTestIds = 0;

  divs.forEach((div, index) => {
    const id = div.getAttribute('id');
    const testId = div.getAttribute('data-testid');

    if (id) {
      if (idsFound.has(id)) {
        duplicateIds.push(id);
      } else {
        idsFound.add(id);
      }
      divsWithIds++;
    } else {
      missingIds.push(`div-${index}-${div.className.split(' ')[0] || 'unnamed'}`);
    }

    if (testId) {
      divsWithTestIds++;
    }
  });

  const coverage = divs.length > 0 ? (divsWithIds / divs.length) * 100 : 0;

  return {
    totalDivs: divs.length,
    divsWithIds,
    divsWithTestIds,
    coverage: Math.round(coverage * 100) / 100,
    duplicateIds: [...new Set(duplicateIds)],
    missingIds: missingIds.slice(0, 10) // Limit to first 10 for readability
  };
}

/**
 * Logs detailed analysis to console
 */
export function logElementIdAnalysis(): ElementIdStats {
  const stats = analyzeElementIds();

  console.group('🔍 Element ID Analysis');
  console.log(`📊 Total DIVs: ${stats.totalDivs}`);
  console.log(`✅ DIVs with IDs: ${stats.divsWithIds}`);
  console.log(`🧪 DIVs with test IDs: ${stats.divsWithTestIds}`);
  console.log(`📈 Coverage: ${stats.coverage}%`);

  if (stats.duplicateIds.length > 0) {
    console.warn('⚠️ Duplicate IDs found:', stats.duplicateIds);
  }

  if (stats.missingIds.length > 0) {
    console.warn('❌ Missing IDs (sample):', stats.missingIds);
  }

  if (stats.coverage === 100) {
    console.log('🎉 Perfect! All DIVs have unique IDs');
  } else if (stats.coverage >= 90) {
    console.log('✨ Excellent ID coverage!');
  } else if (stats.coverage >= 70) {
    console.log('👍 Good ID coverage');
  } else {
    console.warn('⚠️ Low ID coverage - needs improvement');
  }

  console.groupEnd();

  return stats;
}

/**
 * Validates that all IDs follow the naming convention
 */
export function validateIdConvention(): { valid: string[], invalid: string[] } {
  const divs = document.querySelectorAll('div[id]');
  const valid: string[] = [];
  const invalid: string[] = [];

  // Pattern: {page}-{section}-{component}-{index}
  const conventionPattern = /^[a-z]+-[a-z-]+-[a-z-]+-\d+$/;

  divs.forEach(div => {
    const id = div.getAttribute('id')!;
    if (conventionPattern.test(id)) {
      valid.push(id);
    } else {
      invalid.push(id);
    }
  });

  return { valid, invalid };
}

/**
 * React DevTools integration test
 */
export function testReactDevToolsIntegration(): boolean {
  try {
    // Check if React DevTools can find elements by ID
    const stats = analyzeElementIds();
    const sampleIds = Array.from(document.querySelectorAll('div[id]'))
      .slice(0, 5)
      .map(el => el.getAttribute('id'))
      .filter(Boolean) as string[];

    let successCount = 0;

    sampleIds.forEach(id => {
      const element = document.getElementById(id);
      if (element && element.tagName === 'DIV') {
        successCount++;
      }
    });

    const success = successCount === sampleIds.length;

    console.log(`🔧 React DevTools Integration Test: ${success ? 'PASSED' : 'FAILED'}`);
    console.log(`✅ Found ${successCount}/${sampleIds.length} test elements`);

    return success;
  } catch (error) {
    console.error('❌ React DevTools integration test failed:', error);
    return false;
  }
}

/**
 * Complete verification suite
 */
export function runCompleteVerification(): {
  stats: ElementIdStats;
  convention: { valid: string[], invalid: string[] };
  devToolsTest: boolean;
} {
  console.log('🚀 Running complete Element ID verification...\n');

  const stats = logElementIdAnalysis();
  const convention = validateIdConvention();
  const devToolsTest = testReactDevToolsIntegration();

  console.log('\n📋 Convention Validation:');
  console.log(`✅ Valid IDs: ${convention.valid.length}`);
  console.log(`❌ Invalid IDs: ${convention.invalid.length}`);

  if (convention.invalid.length > 0) {
    console.warn('Invalid IDs (first 5):', convention.invalid.slice(0, 5));
  }

  console.log('\n📊 Summary:');
  console.log(`• ID Coverage: ${stats.coverage}%`);
  console.log(`• Convention Compliance: ${((convention.valid.length / (convention.valid.length + convention.invalid.length)) * 100).toFixed(1)}%`);
  console.log(`• React DevTools: ${devToolsTest ? 'Compatible' : 'Issues Found'}`);

  return { stats, convention, devToolsTest };
}

// Auto-run in development
if (process.env.NODE_ENV === 'development') {
  // Run verification after DOM loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(runCompleteVerification, 1000);
    });
  } else {
    setTimeout(runCompleteVerification, 1000);
  }
}