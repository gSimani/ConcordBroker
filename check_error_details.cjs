const puppeteer = require('puppeteer');

async function checkErrorDetails() {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    const consoleMessages = [];
    const errors = [];

    // Capture all console messages
    page.on('console', msg => {
        consoleMessages.push({
            type: msg.type(),
            text: msg.text(),
            location: msg.location(),
            timestamp: new Date().toISOString()
        });
    });

    // Capture page errors
    page.on('pageerror', error => {
        errors.push({
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
    });

    // Capture request failures
    page.on('requestfailed', request => {
        console.log(`❌ Request failed: ${request.url()} - ${request.failure()?.errorText}`);
    });

    try {
        console.log('🔍 Loading properties page to check error details...');

        await page.goto('http://localhost:5173/properties', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait for any async errors
        await new Promise(resolve => setTimeout(resolve, 5000));

        // Try to get error details from the error boundary
        const errorDetails = await page.evaluate(() => {
            const errorContainer = document.querySelector('[data-testid="error-boundary-container"]');
            if (errorContainer) {
                const details = errorContainer.querySelector('details');
                if (details) {
                    // Open details to get full error
                    details.open = true;
                    return {
                        hasError: true,
                        errorText: errorContainer.innerText,
                        errorHTML: errorContainer.innerHTML
                    };
                }
            }
            return { hasError: false };
        });

        console.log('\n📊 Error Analysis:');
        console.log(`Errors captured: ${errors.length}`);
        console.log(`Console messages: ${consoleMessages.length}`);
        console.log(`Error boundary active: ${errorDetails.hasError}`);

        if (errorDetails.hasError) {
            console.log('\n🚨 Error Boundary Details:');
            console.log(errorDetails.errorText);
        }

        console.log('\n📝 Console Messages:');
        consoleMessages.forEach((msg, i) => {
            console.log(`${i + 1}. [${msg.type}] ${msg.text}`);
            if (msg.location && (msg.location.url || msg.location.lineNumber)) {
                console.log(`   Location: ${msg.location.url}:${msg.location.lineNumber}`);
            }
        });

        if (errors.length > 0) {
            console.log('\n💥 Page Errors:');
            errors.forEach((error, i) => {
                console.log(`${i + 1}. ${error.message}`);
                if (error.stack) {
                    console.log(`   Stack: ${error.stack}`);
                }
            });
        }

        // Check if the page loaded any content at all
        const pageContent = await page.evaluate(() => {
            return {
                title: document.title,
                bodyText: document.body.innerText.substring(0, 500),
                elementsCount: document.querySelectorAll('*').length,
                hasRoot: !!document.getElementById('root'),
                hasReactContent: document.body.innerHTML.includes('react') || document.body.innerHTML.includes('React')
            };
        });

        console.log('\n📄 Page Content Analysis:');
        console.log(`Title: ${pageContent.title}`);
        console.log(`Elements: ${pageContent.elementsCount}`);
        console.log(`Has root: ${pageContent.hasRoot}`);
        console.log(`React content: ${pageContent.hasReactContent}`);
        console.log(`Body text: ${pageContent.bodyText}`);

        // Try to check if it's a specific dependency issue
        const dependencyCheck = await page.evaluate(() => {
            // Check if key dependencies are available
            const checks = {
                React: typeof React !== 'undefined',
                ReactDOM: typeof ReactDOM !== 'undefined',
                window: typeof window !== 'undefined',
                document: typeof document !== 'undefined'
            };

            // Check if any specific modules are missing
            let moduleErrors = [];
            try {
                if (window.console && window.console.error) {
                    // Check if there are module resolution errors in the console
                    const errors = window.console._logs || [];
                    moduleErrors = errors.filter(log =>
                        log.includes('Failed to resolve') ||
                        log.includes('Module not found') ||
                        log.includes('Cannot resolve')
                    );
                }
            } catch (e) {}

            return { checks, moduleErrors };
        });

        console.log('\n🔍 Dependency Check:');
        Object.entries(dependencyCheck.checks).forEach(([dep, available]) => {
            console.log(`${available ? '✅' : '❌'} ${dep}: ${available}`);
        });

        if (dependencyCheck.moduleErrors.length > 0) {
            console.log('\n⚠️ Module Errors:');
            dependencyCheck.moduleErrors.forEach((error, i) => {
                console.log(`${i + 1}. ${error}`);
            });
        }

        await page.screenshot({ path: './error_analysis.png', fullPage: true });
        console.log('\n📸 Screenshot saved as error_analysis.png');

        return {
            errors,
            consoleMessages,
            errorDetails,
            pageContent,
            dependencyCheck
        };

    } catch (error) {
        console.error('❌ Error checking failed:', error.message);
    } finally {
        await browser.close();
    }
}

checkErrorDetails().catch(console.error);