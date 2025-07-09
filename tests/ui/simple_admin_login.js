const puppeteer = require('puppeteer');
const assert = require('assert');

// Configuration
const BASE_URL = 'http://127.0.0.1:5051';
const LOGIN_URL = `${BASE_URL}/login`;
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'admin';

// Simplified admin login test
(async () => {
  console.log('Starting Simple Admin Login Test...');
  
  try {
    // Launch browser with some options for better visibility
    const browser = await puppeteer.launch({
      headless: false, // Use actual browser window for debugging
      args: ['--window-size=1280,720'],
      defaultViewport: { width: 1280, height: 720 }
    });
    
    // Create a new page
    const page = await browser.newPage();
    
    // Enable detailed console logging
    page.on('console', msg => console.log(`Browser Console: ${msg.text()}`));
    page.on('response', response => {
      console.log(`Response: ${response.url()} - Status: ${response.status()}`);
    });
    
    // Navigate to the login page
    console.log(`Navigating to ${LOGIN_URL}...`);
    await page.goto(LOGIN_URL, { waitUntil: 'networkidle0' });
    await page.screenshot({ path: 'simple-login-page.png' });
    
    // Fill in admin credentials
    console.log('Entering admin credentials...');
    await page.type('#username', ADMIN_USERNAME);
    await page.type('#password', ADMIN_PASSWORD);
    
    // Take a screenshot before submission
    await page.screenshot({ path: 'simple-before-submit.png' });
    
    // Submit the form and wait
    console.log('Submitting login form...');
    
    // Start listening for responses before clicking
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/login') && response.status() === 200,
      { timeout: 10000 }
    );
    
    // Click the submit button
    await page.click('button[type="submit"]');
    
    // Wait for response
    const response = await responsePromise;
    console.log(`Login response received: ${response.status()}`);
    
    // Wait to see if there are any redirects or state changes
    console.log('Waiting to observe post-login behavior...');
    await page.waitForTimeout(5000);
    
    // Take another screenshot
    await page.screenshot({ path: 'simple-after-submit.png' });
    
    // Get the current URL
    const finalUrl = page.url();
    console.log(`Final URL after login: ${finalUrl}`);
    
    // Check for any indicators of successful login
    const pageContent = await page.content();
    const hasLogoutLink = await page.evaluate(() => {
      return !!document.querySelector('a[href*="logout"]');
    });
    
    console.log(`Logout link present: ${hasLogoutLink}`);
    console.log(`Page contains admin: ${pageContent.includes('admin')}`);
    console.log(`Page contains dashboard: ${pageContent.includes('dashboard') || pageContent.includes('Dashboard')}`);
    
    // Keep browser open for 5 seconds for manual inspection
    await page.waitForTimeout(5000);
    
    // Close the browser
    await browser.close();
    console.log('Test completed.');
    
  } catch (error) {
    console.error('Test failed:', error);
    process.exit(1);
  }
})();
