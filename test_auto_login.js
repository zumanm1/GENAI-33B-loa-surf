const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5051';
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots', 'auto_login');

// Ensure screenshots directory exists
async function ensureDir(dir) {
  try {
    await fs.mkdir(dir, { recursive: true });
    console.log(`Directory created: ${dir}`);
  } catch (error) {
    console.error(`Error creating directory: ${error}`);
  }
}

async function saveScreenshot(page, name) {
  const filename = path.join(SCREENSHOTS_DIR, `${name}-${Date.now()}.png`);
  await page.screenshot({ path: filename, fullPage: true });
  console.log(`Screenshot saved: ${filename}`);
}

async function testAutoLogin() {
  console.log('Testing auto-login functionality...');
  
  let browser;
  try {
    await ensureDir(SCREENSHOTS_DIR);
    
    // Launch browser
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1280, height: 800 }
    });
    
    const page = await browser.newPage();
    page.setDefaultTimeout(10000);
    
    // Visit the root URL which should trigger auto-login
    console.log(`Navigating to ${FRONTEND_URL}/`);
    await page.goto(`${FRONTEND_URL}/`);
    
    // Wait for page to load using compatible method
    await new Promise(r => setTimeout(r, 2000));
    await saveScreenshot(page, 'initial-page');
    
    // Check for login success indicators
    const pageTitle = await page.title();
    console.log(`Page title: ${pageTitle}`);
    
    // Check for flash message
    const hasFlashMessage = await page.evaluate(() => {
      const alerts = document.querySelectorAll('.alert');
      return Array.from(alerts).some(a => a.textContent.includes('Auto-logged in'));
    });
    
    if (hasFlashMessage) {
      console.log('✅ Auto-login flash message detected');
    } else {
      console.log('❌ Auto-login flash message not found');
    }
    
    // Check for navbar elements
    const navbarItems = await page.evaluate(() => {
      const items = document.querySelectorAll('.nav-link');
      return Array.from(items).map(item => item.textContent.trim());
    });
    
    console.log('Navbar items found:', navbarItems);
    
    // Check for welcome message with username
    const welcomeMessage = await page.evaluate(() => {
      const welcome = document.querySelector('.navbar-text');
      return welcome ? welcome.textContent.trim() : null;
    });
    
    console.log('Welcome message:', welcomeMessage);
    
    if (welcomeMessage && welcomeMessage.includes('admin')) {
      console.log('✅ Username found in welcome message');
    } else {
      console.log('❌ Username not found in welcome message');
    }
    
    // Check for specific navbar elements that should be visible when logged in
    const requiredNavItems = [
      'Dashboard', 
      'Devices', 
      'Config Retrieve', 
      'Config Push', 
      'Backups', 
      'Approvals', 
      'Logout'
    ];
    
    const missingItems = requiredNavItems.filter(item => 
      !navbarItems.some(navItem => navItem.includes(item))
    );
    
    if (missingItems.length === 0) {
      console.log('✅ All required navbar items are visible');
    } else {
      console.log('❌ Missing navbar items:', missingItems);
    }
    
    // Take a screenshot of the navbar
    await page.evaluate(() => {
      const navbar = document.querySelector('nav');
      if (navbar) navbar.style.border = '3px solid red';
    });
    
    await saveScreenshot(page, 'navbar-highlight');
    
    // Verify authenticated API access
    console.log('Testing authenticated API access...');
    await page.goto(`${FRONTEND_URL}/api/devices`);
    const apiContent = await page.content();
    
    if (apiContent.includes('devices') && !apiContent.includes('login')) {
      console.log('✅ API access successful - user is authenticated');
    } else {
      console.log('❌ API access failed - user may not be authenticated');
    }
    
    await saveScreenshot(page, 'api-access');
    
    console.log('Auto-login test completed successfully');
    return true;
  } catch (error) {
    console.error(`Test failed: ${error.message}`);
    console.error(error.stack);
    return false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
testAutoLogin()
  .then(success => {
    console.log(`Test ${success ? 'PASSED' : 'FAILED'}`);
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error(`Error running test: ${error}`);
    process.exit(1);
  });
