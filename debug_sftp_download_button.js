/**
 * Comprehensive SFTP Download Button Detection Script
 * Finds download buttons regardless of HTML element type
 */

// 1. Find ALL clickable elements in the toolbar area
function findAllClickableElements() {
    console.log('=== FINDING ALL CLICKABLE ELEMENTS ===');
    
    // Common clickable selectors
    const clickableSelectors = [
        'button',
        'a[href]',
        'input[type="button"]',
        'input[type="submit"]',
        'div[onclick]',
        'span[onclick]',
        '[role="button"]',
        '[tabindex="0"]',
        '.button',
        '.btn',
        '[data-action]',
        '[data-command]'
    ];
    
    const allClickable = [];
    
    clickableSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach((el, index) => {
            allClickable.push({
                element: el,
                tagName: el.tagName,
                selector: selector,
                text: el.textContent?.trim() || '',
                innerHTML: el.innerHTML,
                attributes: Array.from(el.attributes).map(attr => `${attr.name}="${attr.value}"`),
                classes: el.className,
                id: el.id,
                onclick: el.onclick ? 'Has onclick' : 'No onclick',
                parent: el.parentElement?.tagName
            });
        });
    });
    
    console.log(`Found ${allClickable.length} clickable elements:`, allClickable);
    return allClickable;
}

// 2. Find elements with download-related content
function findDownloadElements() {
    console.log('=== SEARCHING FOR DOWNLOAD ELEMENTS ===');
    
    // Download-related keywords
    const downloadKeywords = [
        'download',
        'Download',
        'DOWNLOAD',
        'save',
        'Save',
        'export',
        'Export',
        '⬇', // down arrow
        '↓',
        'dl',
        'get'
    ];
    
    const downloadElements = [];
    
    // Search by text content
    downloadKeywords.forEach(keyword => {
        const elements = document.querySelectorAll('*');
        elements.forEach(el => {
            if (el.textContent?.includes(keyword)) {
                downloadElements.push({
                    element: el,
                    matchType: 'text',
                    keyword: keyword,
                    tagName: el.tagName,
                    text: el.textContent?.trim(),
                    classes: el.className,
                    id: el.id
                });
            }
        });
    });
    
    // Search by attributes
    const attributeSelectors = [
        '[title*="download" i]',
        '[alt*="download" i]',
        '[data-action*="download" i]',
        '[class*="download" i]',
        '[id*="download" i]',
        '[aria-label*="download" i]'
    ];
    
    attributeSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            downloadElements.push({
                element: el,
                matchType: 'attribute',
                selector: selector,
                tagName: el.tagName,
                text: el.textContent?.trim(),
                classes: el.className,
                id: el.id
            });
        });
    });
    
    console.log(`Found ${downloadElements.length} download-related elements:`, downloadElements);
    return downloadElements;
}

// 3. Find toolbar area specifically
function findToolbarElements() {
    console.log('=== ANALYZING TOOLBAR AREA ===');
    
    // Common toolbar selectors
    const toolbarSelectors = [
        '.toolbar',
        '.tool-bar',
        '.action-bar',
        '.button-bar',
        '.menu-bar',
        '[role="toolbar"]',
        '.actions',
        '.controls',
        'nav'
    ];
    
    const toolbars = [];
    
    toolbarSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(toolbar => {
            const toolbarButtons = toolbar.querySelectorAll('*');
            const clickableInToolbar = [];
            
            toolbarButtons.forEach(btn => {
                if (btn.tagName === 'BUTTON' || 
                    btn.tagName === 'A' || 
                    btn.onclick || 
                    btn.getAttribute('role') === 'button' ||
                    btn.classList.contains('button') ||
                    btn.classList.contains('btn')) {
                    clickableInToolbar.push({
                        element: btn,
                        tagName: btn.tagName,
                        text: btn.textContent?.trim(),
                        classes: btn.className,
                        id: btn.id
                    });
                }
            });
            
            toolbars.push({
                toolbar: toolbar,
                selector: selector,
                buttons: clickableInToolbar
            });
        });
    });
    
    console.log('Toolbar analysis:', toolbars);
    return toolbars;
}

// 4. Smart download button finder
function findDownloadButton() {
    console.log('=== SMART DOWNLOAD BUTTON DETECTION ===');
    
    // Get all potentially clickable elements
    const allElements = document.querySelectorAll('*');
    const candidates = [];
    
    allElements.forEach(el => {
        const text = el.textContent?.toLowerCase() || '';
        const title = el.getAttribute('title')?.toLowerCase() || '';
        const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
        const className = el.className?.toLowerCase() || '';
        const id = el.id?.toLowerCase() || '';
        
        // Check if element looks like a download button
        const hasDownloadText = text.includes('download') || 
                               title.includes('download') || 
                               ariaLabel.includes('download') ||
                               className.includes('download') ||
                               id.includes('download');
        
        const isClickable = el.tagName === 'BUTTON' ||
                           el.tagName === 'A' ||
                           el.onclick ||
                           el.getAttribute('role') === 'button' ||
                           className.includes('button') ||
                           className.includes('btn') ||
                           el.style.cursor === 'pointer';
        
        if (hasDownloadText && isClickable) {
            candidates.push({
                element: el,
                tagName: el.tagName,
                text: el.textContent?.trim(),
                title: el.getAttribute('title'),
                ariaLabel: el.getAttribute('aria-label'),
                classes: el.className,
                id: el.id,
                onclick: el.onclick ? 'Has onclick' : 'No onclick'
            });
        }
    });
    
    console.log('Download button candidates:', candidates);
    return candidates;
}

// 5. Click download button (multiple strategies)
function clickDownloadButton() {
    console.log('=== ATTEMPTING TO CLICK DOWNLOAD BUTTON ===');
    
    const candidates = findDownloadButton();
    
    if (candidates.length === 0) {
        console.log('No download button candidates found!');
        return false;
    }
    
    // Try each candidate
    for (let i = 0; i < candidates.length; i++) {
        const candidate = candidates[i];
        console.log(`Trying candidate ${i + 1}:`, candidate);
        
        try {
            // Strategy 1: Direct click
            candidate.element.click();
            console.log('✅ Download button clicked successfully!');
            return true;
        } catch (error) {
            console.log(`❌ Direct click failed:`, error);
            
            try {
                // Strategy 2: Dispatch click event
                candidate.element.dispatchEvent(new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
                console.log('✅ Download button clicked via event dispatch!');
                return true;
            } catch (error2) {
                console.log(`❌ Event dispatch failed:`, error2);
                
                try {
                    // Strategy 3: Execute onclick if available
                    if (candidate.element.onclick) {
                        candidate.element.onclick();
                        console.log('✅ Download button clicked via onclick!');
                        return true;
                    }
                } catch (error3) {
                    console.log(`❌ onclick execution failed:`, error3);
                }
            }
        }
    }
    
    console.log('❌ All click strategies failed');
    return false;
}

// 6. Comprehensive analysis function
function analyzeDownloadButton() {
    console.log('🔍 COMPREHENSIVE DOWNLOAD BUTTON ANALYSIS 🔍');
    
    const results = {
        allClickable: findAllClickableElements(),
        downloadElements: findDownloadElements(),
        toolbarElements: findToolbarElements(),
        downloadCandidates: findDownloadButton()
    };
    
    console.log('📋 ANALYSIS SUMMARY:');
    console.log(`Total clickable elements: ${results.allClickable.length}`);
    console.log(`Download-related elements: ${results.downloadElements.length}`);
    console.log(`Toolbar areas found: ${results.toolbarElements.length}`);
    console.log(`Download button candidates: ${results.downloadCandidates.length}`);
    
    return results;
}

// Execute analysis
const analysis = analyzeDownloadButton();

// Try to click the download button
const clickSuccess = clickDownloadButton();

console.log('🎯 FINAL RESULT:', clickSuccess ? 'SUCCESS' : 'FAILED');