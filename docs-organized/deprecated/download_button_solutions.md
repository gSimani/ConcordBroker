# SFTP Download Button Detection Solutions

## Problem Analysis
- `document.querySelectorAll('button')` only finds 10 buttons
- Download button is visible but not detected as a `<button>` element
- Button appears between "Upload" and "Delete" in toolbar

## Most Likely Solutions

### 1. Anchor Tag Styled as Button
```javascript
// Try these selectors in your browser console:
document.querySelectorAll('a')
document.querySelectorAll('a[onclick]')
document.querySelectorAll('a[href="#"]')
document.querySelectorAll('a:contains("Download")')
```

### 2. Div/Span with Click Handler
```javascript
// Check for divs and spans with click handlers:
document.querySelectorAll('div[onclick]')
document.querySelectorAll('span[onclick]')
document.querySelectorAll('[role="button"]')
```

### 3. Input Element
```javascript
// Check for input buttons:
document.querySelectorAll('input[type="button"]')
document.querySelectorAll('input[type="submit"]')
document.querySelectorAll('input[value*="Download"]')
```

### 4. Class-based Button
```javascript
// Check for elements with button classes:
document.querySelectorAll('.button')
document.querySelectorAll('.btn')
document.querySelectorAll('[class*="download"]')
```

## Quick Browser Console Test

Run this in your browser console to find the Download button:

```javascript
// Comprehensive search
const findDownloadButton = () => {
  const selectors = [
    'button', 'a', 'input[type="button"]', 'input[type="submit"]',
    'div[onclick]', 'span[onclick]', '[role="button"]',
    '.button', '.btn', '[class*="download"]'
  ];
  
  const results = [];
  
  selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      if (el.textContent?.toLowerCase().includes('download') ||
          el.title?.toLowerCase().includes('download') ||
          el.className?.toLowerCase().includes('download')) {
        results.push({
          element: el,
          selector: selector,
          text: el.textContent?.trim(),
          tagName: el.tagName,
          className: el.className,
          title: el.title
        });
      }
    });
  });
  
  console.log('Download button candidates:', results);
  return results;
};

findDownloadButton();
```

## Playwright Selectors for Non-Button Elements

### Text-based Selection
```javascript
// Playwright selectors that work regardless of element type:
page.locator(':has-text("Download")').first()
page.locator('[title*="Download" i]')
page.locator('[aria-label*="Download" i]')
```

### CSS Selector Combinations
```javascript
// Try multiple element types:
page.locator('button:has-text("Download"), a:has-text("Download"), input[value*="Download"], [role="button"]:has-text("Download")')
```

### XPath Selectors
```javascript
// XPath can find any element with text:
page.locator('xpath=//a[contains(text(), "Download")]')
page.locator('xpath=//*[contains(@title, "Download")]')
page.locator('xpath=//*[contains(@class, "download")]')
```

### Position-based Selection
```javascript
// Find by position between Upload and Delete:
page.locator('button:has-text("Upload") + button')  // Next sibling
page.locator('button:has-text("Upload") ~ button')  // Following sibling
```

## Integration Steps

1. **First**: Run the browser console test to identify the element type
2. **Second**: Use the appropriate Playwright selector based on the results
3. **Third**: If still failing, use the JavaScript evaluation approach
4. **Fourth**: As last resort, use position-based detection between Upload/Delete

## Common SFTP Portal Patterns

Most SFTP web portals use one of these patterns:

1. **Anchor tags**: `<a href="#" onclick="download()">Download</a>`
2. **Styled divs**: `<div class="button download-btn" onclick="...">Download</div>`
3. **Input buttons**: `<input type="button" value="Download" onclick="...">`
4. **Icon buttons**: `<a><i class="fa-download"></i></a>`

## Debug Commands

Add these to your Playwright script for debugging:

```python
# See all clickable elements
await page.evaluate('console.log(Array.from(document.querySelectorAll("*")).filter(el => el.onclick || el.tagName === "A" || el.tagName === "BUTTON").map(el => ({tag: el.tagName, text: el.textContent?.trim(), class: el.className})))')

# Check if Download text exists anywhere
await page.evaluate('console.log(document.body.innerHTML.includes("Download"))')

# Get all elements with Download in text
await page.evaluate('console.log(Array.from(document.querySelectorAll("*")).filter(el => el.textContent?.includes("Download")))')
```

## Success Indicators

After clicking, watch for:
- Download dialog appears
- File starts downloading
- URL changes to download endpoint
- Progress indicator shows
- Network activity in DevTools

## Troubleshooting

If the button still isn't found:
1. Check if it's inside an iframe
2. Look for Shadow DOM elements
3. Verify it's not dynamically generated after page load
4. Check if it requires specific file selection first
5. Examine if it's part of a custom JavaScript framework (React, Angular, etc.)