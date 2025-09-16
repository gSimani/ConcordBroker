// Run this in the browser console on http://localhost:5174/properties

console.log('=== Checking Properties Page ===');

// Check if React is loaded
if (window.React) {
    console.log('✓ React is loaded');
} else {
    console.log('✗ React not found');
}

// Check for property cards
const propertyCards = document.querySelectorAll('[class*="property-card"], [class*="MiniPropertyCard"], .card');
console.log(`Found ${propertyCards.length} potential property cards`);

// Check for loading indicators
const loadingElements = document.querySelectorAll('[class*="loading"], [class*="spinner"], .animate-spin');
console.log(`Found ${loadingElements.length} loading indicators`);

// Check for error messages
const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
console.log(`Found ${errorElements.length} error elements`);

// Check for any data in the DOM
const allText = document.body.innerText;
if (allText.includes('WEST PARK') || allText.includes('HOLLYWOOD') || allText.includes('FORT LAUDERDALE')) {
    console.log('✓ Property data found in DOM');
} else {
    console.log('✗ No property data found in DOM');
}

// Check network requests
console.log('\n=== Recent Network Requests ===');
if (window.performance && window.performance.getEntriesByType) {
    const resources = window.performance.getEntriesByType('resource');
    const apiCalls = resources.filter(r => r.name.includes('localhost:8000'));
    apiCalls.forEach(call => {
        console.log(`API Call: ${call.name}`);
        console.log(`  Duration: ${call.duration}ms`);
        console.log(`  Status: ${call.responseStatus || 'unknown'}`);
    });
}

// Check localStorage for cached data
console.log('\n=== LocalStorage ===');
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.includes('property') || key.includes('cache')) {
        const value = localStorage.getItem(key);
        console.log(`${key}: ${value.substring(0, 100)}...`);
    }
}

// Check React DevTools if available
if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
    console.log('\n✓ React DevTools detected');
}

// Try to find the React component tree
const reactRoot = document.getElementById('root');
if (reactRoot && reactRoot._reactRootContainer) {
    console.log('✓ React root found');
}

console.log('\n=== DOM Structure ===');
console.log('Body children:', document.body.children.length);
console.log('Main container:', document.querySelector('#root, .app, main'));

// Check visibility of elements
const visibleElements = Array.from(document.querySelectorAll('*')).filter(el => {
    const style = window.getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetHeight > 0;
});
console.log(`Visible elements: ${visibleElements.length}`);

console.log('\n=== Check complete ===');