/**
 * Admin Login Validation Test using Puppeteer
 * 
 * This test validates the admin login functionality of the Net-Swift Orchestrator.
 * It uses the predefined admin credentials (username: admin, password: admin)
 * and verifies successful login and dashboard access.
 * 
 * Requires:
 *   - Backend running on port 5050
 *   - Frontend running on port 5051
 *   - AI Service running on port 5052
 */

const puppeteer = require('puppeteer');
const assert = require('assert');
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Define the base URL for the frontend application
const BASE_URL = 'http://127.0.0.1:5051';

// Admin credentials
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'admin';

// Function to clean up ports before testing
function cleanupPorts() {
    console.log('\n=== Cleaning up service ports before testing ===');
    try {
        // Try to use our Python port manager if available
        const portManagerPath = path.join(__dirname, '..', '..', 'utils', 'port_manager.py');
        
        if (fs.existsSync(portManagerPath)) {
            console.log('Using port_manager.py utility...');
            execSync(`python ${portManagerPath} free 5050 5051 5052 --force`, { stdio: 'inherit' });
            return true;
        } else {
            console.log('Port manager utility not found, using fallback method...');
            // Fallback to direct command
            const ports = [5050, 5051, 5052];
            
            ports.forEach(port => {
                try {
                    // Find processes on the port
                    const result = execSync(`lsof -i:${port} -t`, { encoding: 'utf8' });
                    
                    if (result.trim()) {
                        // Kill processes
                        const pids = result.trim().split('\n');
                        console.log(`Found processes on port ${port}: ${pids.join(', ')}`);
                        pids.forEach(pid => {
                            if (pid.trim()) {
                                console.log(`Killing process ${pid}...`);
                                execSync(`kill -9 ${pid}`);
                            }
                        });
                    } else {
                        console.log(`Port ${port} is already available`);
                    }
                } catch (err) {
                    // If lsof returns non-zero, the port is likely available
                    console.log(`Port ${port} is already available`);
                }
            });
            return true;
        }
    } catch (error) {
        console.error('Failed to clean up ports:', error);
        return false;
    }
}

// Function to verify services are running
async function checkServices() {
    console.log('\n=== Checking if services are running ===');
    
    const services = [
        { name: 'Backend', url: 'http://127.0.0.1:5050/api/health' },
        { name: 'Frontend', url: 'http://127.0.0.1:5051/login' },
        { name: 'AI Service', url: 'http://127.0.0.1:5052/health' }
    ];
    
    for (const service of services) {
        try {
            console.log(`Checking ${service.name} at ${service.url}...`);
            const response = await fetch(service.url, { timeout: 5000 });
            
            if (response.ok) {
                console.log(`✓ ${service.name} is running`);
            } else {
                console.error(`✗ ${service.name} returned status ${response.status}`);
                return false;
            }
        } catch (error) {
            console.error(`✗ ${service.name} is not reachable: ${error.message}`);
            return false;
        }
    }
    
    return true;
}

// Main test function
(async () => {
    console.log('Starting Admin Login Puppeteer test...');
    
    // Clean up ports before starting
    cleanupPorts();
    
    // Launch browser with some options for better visibility
    const browser = await puppeteer.launch({
        headless: 'new', // Use new headless mode
        args: ['--window-size=1280,720'],
        defaultViewport: { width: 1280, height: 720 }
    });
    
    const page = await browser.newPage();
    
    try {
        // 1. Navigate to the login page
        console.log(`Navigating to ${BASE_URL}/login...`);
        await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle0', timeout: 30000 });

        // Assert the page title
        const pageTitle = await page.title();
        assert.strictEqual(pageTitle, 'Login', `Expected title to be 'Login', but got '${pageTitle}'`);
        console.log('✓ Login page title is correct.');

        // Take screenshot of login page
        await page.screenshot({ path: 'login-page.png' });
        console.log('✓ Login page screenshot saved.');

        // 2. Fill in the login form with admin credentials
        console.log('Filling in admin credentials...');
        await page.type('#username', ADMIN_USERNAME);
        await page.type('#password', ADMIN_PASSWORD);
        console.log('✓ Admin credentials entered.');

        // 3. Click the login button and wait for navigation
        console.log('Clicking login button...');
        await Promise.all([
            page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 30000 }), // Wait for the page to load after login
            page.click('button[type="submit"]') // Click the button
        ]);

        // 4. Verify the URL (should be redirected to dashboard)
        const currentUrl = page.url();
        assert.strictEqual(currentUrl, `${BASE_URL}/`, `Expected URL to be '${BASE_URL}/', but got '${currentUrl}'`);
        console.log('✓ Successfully redirected to dashboard.');

        // 5. Assert that key elements from the dashboard are visible
        console.log('Verifying dashboard content...');
        
        // Look for System Status heading
        const dashboardHeading = await page.$eval("h5", (el) => el.textContent.trim());
        assert.strictEqual(dashboardHeading, 'System Status', `Expected to find 'System Status' heading, but found '${dashboardHeading}'`);
        
        // Verify admin username is displayed
        const userDisplay = await page.$eval(".user-display", (el) => el.textContent.trim());
        assert.ok(userDisplay.includes(ADMIN_USERNAME), `Expected user display to include '${ADMIN_USERNAME}', but got '${userDisplay}'`);
        
        console.log('✓ Dashboard content verified.');
        
        // Take screenshot of dashboard
        await page.screenshot({ path: 'admin-dashboard.png' });
        console.log('✓ Dashboard screenshot saved.');

        console.log('\n\x1b[32m%s\x1b[0m', 'Admin Login Puppeteer test successful: Login and dashboard access verified.');

    } catch (error) {
        console.error('\x1b[31m%s\x1b[0m', 'Admin Login Puppeteer test failed:');
        console.error(error);
        // Take screenshot of failure state
        await page.screenshot({ path: 'test-failure.png' });
        console.log('✓ Failure state screenshot saved.');
        process.exit(1); // Exit with error code
    } finally {
        await browser.close();
    }
})();
