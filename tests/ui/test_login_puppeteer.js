const puppeteer = require('puppeteer');
const assert = require('assert');

// Define the base URL for the frontend application
const BASE_URL = 'http://127.0.0.1:5051';

const crypto = require('crypto');

(async () => {
    console.log('Starting Puppeteer test...');
    const browser = await puppeteer.launch();
    const context = await browser.createIncognitoBrowserContext();
    const page = await context.newPage();

    try {

        // Generate unique credentials
        const testUsername = `testuser_${crypto.randomBytes(4).toString('hex')}`;
        const testPassword = 'a_secure_password';

        // 1. Navigate to the registration page
        console.log(`Navigating to ${BASE_URL}/register...`);
        await page.goto(`${BASE_URL}/register`, { waitUntil: 'networkidle0' });

        // Assert the page title is 'Register'
        const registerTitle = await page.title();
        assert.strictEqual(registerTitle, 'Register', `Expected title to be 'Register', but got '${registerTitle}'`);
        console.log('✓ Register page title is correct.');

        // Fill registration form
        await page.type('#username', testUsername);
        await page.type('#password', testPassword);
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle0' }),
            page.click('button[type="submit"]')
        ]);

        // 2. Verify redirection to login page with success message
        const redirectedUrl = page.url();
        assert.ok(redirectedUrl.includes('/login'), `Expected to be on login page, but got '${redirectedUrl}'`);
        const successAlerts = await page.$$('.alert-success');
        assert.strictEqual(successAlerts.length, 1, `Expected one success alert, but found ${successAlerts.length}`);
        console.log('✓ Registration success message displayed.');

        // 3. Fill in the login form
        console.log(`Navigating to ${BASE_URL}/login...`);
        await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0' });

        // Assert the page title
        const pageTitle = await page.title();
        assert.strictEqual(pageTitle, 'Login', `Expected title to be 'Login', but got '${pageTitle}'`);
        console.log('✓ Page title is correct.');

        // 2. Fill in the login form
        console.log('Filling in login credentials...');
        await page.type('#username', testUsername);
        await page.type('#password', testPassword);
        console.log('✓ Credentials entered.');

        // 3. Click the login button and wait for navigation
        console.log('Clicking login button...');
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle0' }), // Wait for the page to load after login
            page.click('button[type="submit"]') // Click the button
        ]);

        // 4. Verify the URL
        const currentUrl = page.url();
        assert.strictEqual(currentUrl, `${BASE_URL}/`, `Expected URL to be '${BASE_URL}/', but got '${currentUrl}'`);
        console.log('✓ Successfully redirected to dashboard.');

        // 5. Assert that a key element from the dashboard is visible
        console.log('Verifying dashboard content...');
        const dashboardHeading = await page.$eval("h5", (el) => el.textContent.trim());
        assert.strictEqual(dashboardHeading, 'System Status', `Expected to find 'System Status' heading, but found '${dashboardHeading}'`);
        console.log('✓ Dashboard content verified.');

        console.log('\n\x1b[32m%s\x1b[0m', 'Puppeteer test successful: Login and dashboard view verified.');

    } catch (error) {
        console.error('\x1b[31m%s\x1b[0m', 'Puppeteer test failed:');
        console.error(error);
        process.exit(1); // Exit with error code
    } finally {
        await browser.close();
    }
})();
