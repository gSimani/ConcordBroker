/**
 * Playwright Download Button Detection and Click
 * Use this code within your Playwright script
 */

async function findAndClickDownloadButton(page) {
    console.log('🔍 Searching for Download button...');
    
    // Strategy 1: Try common download button selectors
    const downloadSelectors = [
        'button:has-text("Download")',
        'button:has-text("download")',
        'a:has-text("Download")',
        'a:has-text("download")',
        '[role="button"]:has-text("Download")',
        '[role="button"]:has-text("download")',
        'input[type="button"][value*="Download" i]',
        'input[type="submit"][value*="Download" i]',
        '.button:has-text("Download")',
        '.btn:has-text("Download")',
        '[title*="Download" i]',
        '[aria-label*="Download" i]',
        '[data-action*="download" i]'
    ];
    
    for (const selector of downloadSelectors) {
        try {
            const element = await page.locator(selector).first();
            if (await element.isVisible()) {
                console.log(`✅ Found download button with selector: ${selector}`);
                await element.click();
                return true;
            }
        } catch (error) {
            // Continue to next selector
        }
    }
    
    // Strategy 2: Find elements by position (between Upload and Delete)
    console.log('🎯 Searching by toolbar position...');
    try {
        // Look for Upload button, then find next sibling
        const uploadButton = await page.locator('button:has-text("Upload"), a:has-text("Upload"), [title*="Upload" i]').first();
        if (await uploadButton.isVisible()) {
            // Try next sibling
            const nextSibling = uploadButton.locator('xpath=following-sibling::*[1]');
            if (await nextSibling.isVisible()) {
                console.log('✅ Found element after Upload button');
                await nextSibling.click();
                return true;
            }
        }
    } catch (error) {
        console.log('❌ Position-based search failed:', error);
    }
    
    // Strategy 3: Use JavaScript evaluation to find all clickable elements
    console.log('🔬 Using JavaScript evaluation...');
    try {
        const downloadButton = await page.evaluate(() => {
            // Find all potentially clickable elements
            const allElements = document.querySelectorAll('*');
            const candidates = [];
            
            for (let el of allElements) {
                const text = el.textContent?.toLowerCase() || '';
                const title = el.getAttribute('title')?.toLowerCase() || '';
                const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
                const className = el.className?.toLowerCase() || '';
                
                const hasDownloadText = text.includes('download') || 
                                       title.includes('download') || 
                                       ariaLabel.includes('download') ||
                                       className.includes('download');
                
                const isClickable = el.tagName === 'BUTTON' ||
                                   el.tagName === 'A' ||
                                   el.onclick ||
                                   el.getAttribute('role') === 'button' ||
                                   className.includes('button') ||
                                   className.includes('btn') ||
                                   getComputedStyle(el).cursor === 'pointer';
                
                if (hasDownloadText && isClickable) {
                    candidates.push({
                        element: el,
                        text: el.textContent?.trim(),
                        tagName: el.tagName,
                        xpath: getElementXPath(el)
                    });
                }
            }
            
            // Helper function to get XPath
            function getElementXPath(element) {
                if (element.id !== '') {
                    return `//*[@id="${element.id}"]`;
                }
                if (element === document.body) {
                    return '/html/body';
                }
                let ix = 0;
                const siblings = element.parentNode.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return getElementXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return candidates.length > 0 ? candidates[0] : null;
        });
        
        if (downloadButton) {
            console.log(`✅ Found download button via JS evaluation:`, downloadButton);
            await page.locator(`xpath=${downloadButton.xpath}`).click();
            return true;
        }
    } catch (error) {
        console.log('❌ JavaScript evaluation failed:', error);
    }
    
    // Strategy 4: Find by icon or image
    console.log('🎨 Searching by icons...');
    const iconSelectors = [
        '[src*="download" i]',
        '[class*="download" i]',
        '[class*="arrow-down" i]',
        '[class*="fa-download" i]',
        'svg[class*="download" i]',
        'i[class*="download" i]'
    ];
    
    for (const selector of iconSelectors) {
        try {
            // Find the icon, then look for its clickable parent
            const icon = await page.locator(selector).first();
            if (await icon.isVisible()) {
                // Try clicking the icon itself
                await icon.click();
                return true;
            }
        } catch (error) {
            // Try parent elements
            try {
                const iconParent = await page.locator(selector).first().locator('..');
                if (await iconParent.isVisible()) {
                    await iconParent.click();
                    return true;
                }
            } catch (parentError) {
                // Continue to next selector
            }
        }
    }
    
    // Strategy 5: Comprehensive toolbar analysis
    console.log('🧰 Analyzing toolbar structure...');
    try {
        const toolbarButtons = await page.evaluate(() => {
            // Look for common toolbar containers
            const toolbarSelectors = ['.toolbar', '.tool-bar', '.action-bar', '.button-bar', '[role="toolbar"]', '.actions', '.controls'];
            const toolbars = [];
            
            toolbarSelectors.forEach(selector => {
                const containers = document.querySelectorAll(selector);
                containers.forEach(container => {
                    const buttons = container.querySelectorAll('*');
                    buttons.forEach((btn, index) => {
                        if (btn.tagName === 'BUTTON' || 
                            btn.tagName === 'A' || 
                            btn.onclick || 
                            btn.getAttribute('role') === 'button' ||
                            btn.classList.contains('button') ||
                            btn.classList.contains('btn')) {
                            
                            toolbars.push({
                                index: index,
                                text: btn.textContent?.trim(),
                                tagName: btn.tagName,
                                className: btn.className,
                                title: btn.getAttribute('title'),
                                xpath: getElementXPath(btn)
                            });
                        }
                    });
                });
            });
            
            function getElementXPath(element) {
                if (element.id !== '') {
                    return `//*[@id="${element.id}"]`;
                }
                if (element === document.body) {
                    return '/html/body';
                }
                let ix = 0;
                const siblings = element.parentNode.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return getElementXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return toolbars;
        });
        
        console.log('Found toolbar buttons:', toolbarButtons);
        
        // Look for button between Upload and Delete
        const uploadIndex = toolbarButtons.findIndex(btn => 
            btn.text?.toLowerCase().includes('upload') || 
            btn.title?.toLowerCase().includes('upload')
        );
        
        const deleteIndex = toolbarButtons.findIndex(btn => 
            btn.text?.toLowerCase().includes('delete') || 
            btn.title?.toLowerCase().includes('delete')
        );
        
        if (uploadIndex >= 0 && deleteIndex >= 0 && deleteIndex > uploadIndex) {
            // Try buttons between upload and delete
            for (let i = uploadIndex + 1; i < deleteIndex; i++) {
                try {
                    await page.locator(`xpath=${toolbarButtons[i].xpath}`).click();
                    console.log(`✅ Clicked button at position ${i} between Upload and Delete`);
                    return true;
                } catch (error) {
                    console.log(`❌ Failed to click button at position ${i}:`, error);
                }
            }
        }
    } catch (error) {
        console.log('❌ Toolbar analysis failed:', error);
    }
    
    console.log('❌ All strategies failed to find Download button');
    return false;
}

// Alternative: Get all elements and their info for manual inspection
async function debugAllElements(page) {
    console.log('🐛 DEBUG: Getting all elements info...');
    
    const allElements = await page.evaluate(() => {
        const elements = [];
        const allTags = document.querySelectorAll('*');
        
        allTags.forEach((el, index) => {
            if (el.offsetWidth > 0 && el.offsetHeight > 0) { // Only visible elements
                elements.push({
                    index: index,
                    tagName: el.tagName,
                    text: el.textContent?.trim().substring(0, 50),
                    className: el.className,
                    id: el.id,
                    title: el.getAttribute('title'),
                    ariaLabel: el.getAttribute('aria-label'),
                    onclick: el.onclick ? 'Has onclick' : null,
                    role: el.getAttribute('role'),
                    type: el.getAttribute('type'),
                    value: el.getAttribute('value'),
                    href: el.getAttribute('href')
                });
            }
        });
        
        return elements;
    });
    
    console.log('All visible elements:', allElements);
    return allElements;
}

// Export functions for use in your main script
module.exports = {
    findAndClickDownloadButton,
    debugAllElements
};

// If running standalone, export to global
if (typeof window !== 'undefined') {
    window.findAndClickDownloadButton = findAndClickDownloadButton;
    window.debugAllElements = debugAllElements;
}