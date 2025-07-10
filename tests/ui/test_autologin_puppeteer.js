const puppeteer = require('puppeteer');
const assert = require('assert');

const BASE_URL = 'http://127.0.0.1:5051';

(async () => {
    console.log('Starting auto-login validation test...');
    const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();

    try {
        console.log(`Navigating to ${BASE_URL}/ to test auto-login...`);
        await page.goto(BASE_URL, { waitUntil: 'networkidle2' });

        // After auto-login, the URL should be the dashboard
        const finalUrl = page.url();
        assert.strictEqual(finalUrl, `${BASE_URL}/`, `Expected URL to be ${BASE_URL}/, but got ${finalUrl}`);
        console.log('✓ Successfully navigated to the dashboard.');

        // Verify that the 'admin' user is displayed in the navbar
        console.log('Verifying dashboard content for auto-logged-in user...');
        const usernameDisplay = await page.$eval('.navbar-text', el => el.textContent);
        assert.ok(usernameDisplay.includes('admin'), `Expected to see 'admin' user, but got '${usernameDisplay}'`);
        console.log('✓ Auto-login successful, admin user is logged in.');

        console.log('Puppeteer auto-login test passed!');

    } catch (error) {
        console.error('Puppeteer test failed:', error.message);
        await page.screenshot({ path: 'autologin-test-failure.png' });
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
