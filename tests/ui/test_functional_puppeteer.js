/**
 * Net-Swift Orchestrator - Functional Test Suite with Puppeteer
 * 
 * This test suite performs comprehensive functional testing of the application
 * using Puppeteer. It tests the integration between all services:
 * - Backend API (port 5050)
 * - Frontend UI (port 5051)
 * - AI Service (port 5004)
 * 
 * To run this test:
 * 1. Start the test environment: ./start_test_env.sh
 * 2. Run the test: node tests/ui/test_functional_puppeteer.js
 */

const puppeteer = require('puppeteer');
const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5051';
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:5050';
const AI_AGENT_URL = process.env.AI_AGENT_URL || 'http://127.0.0.1:5004';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

// Ensure screenshot directory exists
async function ensureScreenshotDir() {
  try {
    await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
  } catch (error) {
    console.error('Error creating screenshot directory:', error);
  }
}

// Take screenshot with timestamp
async function takeScreenshot(page, name) {
  await ensureScreenshotDir();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = path.join(SCREENSHOT_DIR, `${name}-${timestamp}.png`);
  await page.screenshot({ path: filename, fullPage: true });
  console.log(`Screenshot saved: ${filename}`);
  return filename;
}

// Check if services are running before proceeding
async function checkServices() {
  console.log('Checking if all services are running before starting tests...');
  
  try {
    // Check backend
    const backendResponse = await axios.get(`${BACKEND_URL}/api/health`, { timeout: 5000 });
    console.log('Backend status:', backendResponse.status, backendResponse.data?.status || '');
    
    if (backendResponse.status !== 200) {
      throw new Error(`Backend health check failed with status ${backendResponse.status}`);
    }
    
    // Check frontend
    const frontendResponse = await axios.get(FRONTEND_URL, { timeout: 5000 });
    console.log('Frontend status:', frontendResponse.status);
    
    if (frontendResponse.status !== 200) {
      throw new Error(`Frontend check failed with status ${frontendResponse.status}`);
    }
    
    // Check AI service
    const aiResponse = await axios.get(`${AI_AGENT_URL}/health`, { timeout: 5000 });
    console.log('AI service status:', aiResponse.status, aiResponse.data?.status || '');
    
    if (aiResponse.status !== 200) {
      throw new Error(`AI service health check failed with status ${aiResponse.status}`);
    }

    // Check that the AI service is correctly running in mock mode for tests
    if (!aiResponse.data || !aiResponse.data.status || !aiResponse.data.timestamp) {
      console.warn('Warning: AI service response may not match expected format');
    }
    
    return true;
  } catch (error) {
    console.error('Service check failed:', error.message);
    return false;
  }
}

// Run the full test suite
async function runTests() {
  // Validate service health before starting
  const servicesRunning = await checkServices();
  if (!servicesRunning) {
    console.error('❌ ERROR: Required services are not running. Please start them with ./start_test_env.sh');
    process.exit(1);
  }

  console.log('✅ All services verified running. Starting browser tests...');

  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',  // Use new headless mode
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      defaultViewport: { width: 1280, height: 800 }
    });
    
    // Run test scenarios
    await testAdminLogin(browser);
    await testDashboardAccess(browser);
    await testDevicesList(browser);
    await testAIServiceIntegration(browser);
    
    console.log('✅ All tests completed successfully!');
  } catch (error) {
    console.error('❌ Test failure:', error);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Test scenario: Admin login
async function testAdminLogin(browser) {
  console.log('\n🔍 Running Test: Admin Login');
  const page = await browser.newPage();
  
  try {
    // Navigate to login page
    await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle0' });
    console.log('  Navigated to login page');
    await takeScreenshot(page, 'admin-login-page');
    
    // Fill and submit login form
    await page.type('#username', 'admin');
    await page.type('#password', 'admin');
    console.log('  Filled login form with admin credentials');
    
    // Submit the form
    const form = await page.$('#loginForm');
    await form.evaluate(form => form.submit());
    console.log('  Submitted login form');
    
    // Wait for navigation to complete
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
    console.log('  Navigation completed after form submission');
    
    // Take screenshot after login
    await takeScreenshot(page, 'admin-after-login');
    
    // Check for success indicators
    const successAlert = await page.$('.alert-success');
    const welcomeText = await page.evaluate(() => {
      const el = document.querySelector('.alert-success');
      return el ? el.textContent : null;
    });
    
    if (welcomeText && welcomeText.includes('Welcome back')) {
      console.log('  ✅ Success: Login successful message displayed');
    } else {
      throw new Error('Login success message not displayed');
    }
    
    // Verify we're on the dashboard page
    const url = page.url();
    if (!url.includes('/index') && !url.endsWith('/')) {
      throw new Error(`Not redirected to dashboard. Current URL: ${url}`);
    }
    console.log(`  ✅ Redirected to dashboard: ${url}`);
    
    // Check for session cookies
    const cookies = await page.cookies();
    const hasSessionCookie = cookies.some(cookie => cookie.name.includes('session'));
    if (!hasSessionCookie) {
      throw new Error('No session cookie found after login');
    }
    console.log('  ✅ Session cookie verified');
    
  } catch (error) {
    await takeScreenshot(page, 'admin-login-error');
    throw error;
  } finally {
    await page.close();
  }
}

// Test scenario: Dashboard access
async function testDashboardAccess(browser) {
  console.log('\n🔍 Running Test: Dashboard Access');
  const page = await browser.newPage();
  
  try {
    // Set cookies from previous login
    const adminPage = await browser.newPage();
    await adminPage.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle0' });
    await adminPage.type('#username', 'admin');
    await adminPage.type('#password', 'admin');
    const form = await adminPage.$('#loginForm');
    await form.evaluate(form => form.submit());
    await adminPage.waitForNavigation({ waitUntil: 'networkidle0' });
    
    // Get cookies from admin page
    const cookies = await adminPage.cookies();
    await adminPage.close();
    
    // Apply cookies to test page
    for (const cookie of cookies) {
      await page.setCookie(cookie);
    }
    
    // Navigate to dashboard
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle0' });
    console.log('  Navigated to dashboard');
    await takeScreenshot(page, 'dashboard');
    
    // Verify dashboard elements
    const dashboardElements = [
      'System Status',
      'Managed Devices',
      'Recent Activity'
    ];
    
    for (const element of dashboardElements) {
      const hasElement = await page.evaluate(text => {
        return document.body.innerText.includes(text);
      }, element);
      
      if (hasElement) {
        console.log(`  ✅ Dashboard contains "${element}"`);
      } else {
        throw new Error(`Dashboard missing element: ${element}`);
      }
    }
    
  } catch (error) {
    await takeScreenshot(page, 'dashboard-error');
    throw error;
  } finally {
    await page.close();
  }
}

// Test scenario: Devices list
async function testDevicesList(browser) {
  console.log('\n🔍 Running Test: Devices List');
  const page = await browser.newPage();
  
  try {
    // Set cookies from previous login
    const adminPage = await browser.newPage();
    await adminPage.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle0' });
    await adminPage.type('#username', 'admin');
    await adminPage.type('#password', 'admin');
    const form = await adminPage.$('#loginForm');
    await form.evaluate(form => form.submit());
    await adminPage.waitForNavigation({ waitUntil: 'networkidle0' });
    
    // Get cookies from admin page
    const cookies = await adminPage.cookies();
    await adminPage.close();
    
    // Apply cookies to test page
    for (const cookie of cookies) {
      await page.setCookie(cookie);
    }
    
    // Navigate to devices page
    await page.goto(`${FRONTEND_URL}/devices`, { waitUntil: 'networkidle0' });
    console.log('  Navigated to devices page');
    await takeScreenshot(page, 'devices-list');
    
    // Check for devices table
    const hasTable = await page.evaluate(() => {
      return !!document.querySelector('table');
    });
    
    if (hasTable) {
      console.log('  ✅ Devices table found');
    } else {
      throw new Error('Devices table not found');
    }
    
  } catch (error) {
    await takeScreenshot(page, 'devices-list-error');
    throw error;
  } finally {
    await page.close();
  }
}

// Test scenario: AI Service Integration
async function testAIServiceIntegration(browser) {
  console.log('\n🔍 Running Test: AI Service Integration');
  
  try {
    // Direct API test of AI service
    const response = await axios.post(`${AI_AGENT_URL}/api/rag_query`, {
      query: 'Test query for RAG'
    }, { timeout: 5000 });
    
    console.log('  AI service RAG query response status:', response.status);
    
    if (response.status !== 200) {
      throw new Error(`AI service RAG query failed with status ${response.status}`);
    }
    
    // Check response data
    if (!response.data || !response.data.response) {
      throw new Error('AI service response missing expected data');
    }
    
    console.log('  ✅ AI service integration verified');
    console.log(`  Response: "${response.data.response.substring(0, 50)}..."`);
    
  } catch (error) {
    console.error('  ❌ AI service test failed:', error.message);
    throw new Error(`AI service integration test failed: ${error.message}`);
  }
}

// Main entry point
(async () => {
  try {
    await runTests();
    console.log('\n✅ All functional tests passed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('\n❌ Functional tests failed:', error);
    process.exit(1);
  }
})();
