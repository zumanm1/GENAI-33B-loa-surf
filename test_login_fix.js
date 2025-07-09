const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

// Configuration
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5051';
const USERNAME = 'admin';
const PASSWORD = 'admin';

// Create a directory for screenshots
const screenshotsDir = path.join(__dirname, 'screenshots');

async function ensureScreenshotsDir() {
  try {
    await fs.mkdir(screenshotsDir, { recursive: true });
  } catch (error) {
    console.error(`Error creating screenshots directory: ${error.message}`);
  }
}

async function takeScreenshot(page, name) {
  try {
    await page.screenshot({ 
      path: path.join(screenshotsDir, `${name}-${Date.now()}.png`),
      fullPage: true 
    });
    console.log(`✅ Screenshot saved: ${name}`);
  } catch (error) {
    console.error(`❌ Failed to take screenshot: ${error.message}`);
  }
}

async function testLogin() {
  console.log('Starting login test...');
  let browser;

  try {
    await ensureScreenshotsDir();

    // Launch the browser and open a new page
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1280, height: 800 }
    });
    const page = await browser.newPage();
    page.setDefaultTimeout(10000);
    
    // Go to login page
    console.log(`Navigating to login page at ${FRONTEND_URL}/login`);
    await page.goto(`${FRONTEND_URL}/login`);
    await takeScreenshot(page, 'login-page');

    // Fill in login form
    console.log(`Filling login form with username: ${USERNAME}`);
    await page.type('#username', USERNAME);
    await page.type('#password', PASSWORD);
    
    // Take screenshot before clicking login
    await takeScreenshot(page, 'before-login');
    
    // Click the login button and wait for navigation
    console.log('Submitting login form...');
    await Promise.all([
      page.click('button[type="submit"]'),
      page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 5000 }).catch(() => {
        console.log('Navigation may not have occurred, continuing...');
      })
    ]);

    // Take a screenshot after login attempt
    await takeScreenshot(page, 'after-login');

    // Get cookies and analyze them
    const cookies = await page.cookies();
    console.log('Cookies after login:');
    for (const cookie of cookies) {
      console.log(`- ${cookie.name}: ${cookie.value.substring(0, 10)}...`);
    }

    // Check if we have authentication cookies
    const authCookie = cookies.find(c => c.name === 'auth_token');
    const sessionCookie = cookies.find(c => c.name.includes('session'));
    
    if (authCookie || sessionCookie) {
      console.log('✅ Authentication cookies found - login successful');
    } else {
      console.log('❌ No authentication cookies found - login may have failed');
    }

    // Check page URL and content for success indicators
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);
    
    // Analyze current page content
    const pageText = await page.$eval('body', el => el.innerText);
    const navItems = await page.$$eval('.nav-link', items => items.map(i => i.innerText));
    
    console.log('Navigation items found:', navItems);
    
    // Check if we see dashboard elements
    if (pageText.includes('System Status') || pageText.includes('Managed Devices')) {
      console.log('✅ Dashboard elements found - login successful');
    } else {
      console.log('❌ Dashboard elements not found - login may have failed');
    }

    // Check if login form is still visible
    const loginFormVisible = await page.$('#loginForm').then(el => !!el).catch(() => false);
    if (!loginFormVisible) {
      console.log('✅ Login form no longer visible - login successful');
    } else {
      console.log('❌ Login form still visible - login likely failed');
    }

    // Test API access with session
    console.log('Testing API access to verify session...');
    try {
      // Get current page cookies and set for axios
      const pageUrl = new URL(page.url());
      const domain = pageUrl.hostname;
      
      const axiosCookieStr = cookies
        .filter(c => c.domain === domain || c.domain === '')
        .map(c => `${c.name}=${c.value}`)
        .join('; ');
      
      const response = await axios.get(`${FRONTEND_URL}/api/devices`, {
        headers: {
          Cookie: axiosCookieStr
        }
      });
      
      console.log('API response status:', response.status);
      console.log('API data received:', response.data ? 'Yes' : 'No');
      if (response.status === 200) {
        console.log('✅ API access successful with session cookies');
      }
    } catch (error) {
      console.error('❌ API access failed:', error.message);
    }

    // Test events endpoint which was previously failing
    try {
      const eventResponse = await axios.get(`${FRONTEND_URL}/api/events`, {
        headers: {
          Cookie: cookies.map(c => `${c.name}=${c.value}`).join('; ')
        }
      });
      
      console.log('Events API status:', eventResponse.status);
      console.log('Events data:', JSON.stringify(eventResponse.data).substring(0, 100) + '...');
      if (eventResponse.status === 200) {
        console.log('✅ Events API access successful');
      }
    } catch (error) {
      console.error('❌ Events API access failed:', error.message);
    }

    // Take final screenshot of the dashboard
    await takeScreenshot(page, 'dashboard');
    console.log('Login test completed.');
    
    return true;
  } catch (error) {
    console.error(`❌ Test failed with error: ${error.message}`);
    console.error(error.stack);
    return false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
testLogin().then(success => {
  console.log(`Test ${success ? 'passed' : 'failed'}`);
  process.exit(success ? 0 : 1);
});
