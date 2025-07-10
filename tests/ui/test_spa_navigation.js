const puppeteer = require('puppeteer');
const assert = require('assert');

const BASE_URL = 'http://127.0.0.1:5051';
const VIEWS = ['configuration', 'chat', 'documents', 'network-ops', 'analytics'];

(async () => {
    console.log('Starting SPA Navigation Puppeteer test...');
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    try {
        // 1. Login to the application
        console.log(`Navigating to ${BASE_URL}/login...`);
        await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0' });

        console.log('Waiting for login form...');
        try {
            await page.waitForSelector('#username', { timeout: 5000 });
        } catch (e) {
            console.error('Could not find login form.');
            await page.screenshot({ path: 'login_failure.png' });
            console.log('Screenshot saved to login_failure.png');
            throw e;
        }

        console.log('Filling in login credentials...');
        await page.type('#username', 'admin');
        await page.type('#password', 'admin');

        console.log('Clicking login button...');
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle0' }),
            page.click('button[type="submit"]')
        ]);

        // 2. Navigate to the SPA page
        const spaUrl = `${BASE_URL}/genai_networks_engineer`;
        console.log(`Navigating to ${spaUrl}...`);
        await page.goto(spaUrl, { waitUntil: 'networkidle0' });

        // 3. Test each view
        for (const view of VIEWS) {
            console.log(`\n--- Testing view: #${view} ---`);
            const viewUrl = `${spaUrl}#${view}`;
            await page.goto(viewUrl, { waitUntil: 'networkidle0' });

            // Wait for the view router to do its job
            await page.waitForTimeout(500);

            const activeViewId = `#${view}-view`;
            const isVisible = await page.evaluate((selector) => {
                const elem = document.querySelector(selector);
                if (!elem) return false;
                // Check if the element is visible (not having d-none class)
                return !elem.classList.contains('d-none');
            }, activeViewId);

            assert.ok(isVisible, `View '${view}' should be visible.`);
            console.log(`✓ View '${view}' is visible.`);

            // Verify other views are hidden
            for (const otherView of VIEWS) {
                if (otherView !== view) {
                    const otherViewId = `#${otherView}-view`;
                    const isOtherVisible = await page.evaluate((selector) => {
                        const elem = document.querySelector(selector);
                        if (!elem) return false;
                        return !elem.classList.contains('d-none');
                    }, otherViewId);
                    assert.strictEqual(isOtherVisible, false, `View '${otherView}' should be hidden when '${view}' is active.`);
                }
            }
            console.log(`✓ Other views are correctly hidden.`);
        }

        console.log('\n\x1b[32m%s\x1b[0m', 'Puppeteer SPA Navigation test successful: All views load correctly.');

    } catch (error) {
        console.error('\x1b[31m%s\x1b[0m', 'Puppeteer test failed:');
        console.error(error);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
