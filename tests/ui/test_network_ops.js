const puppeteer = require('puppeteer');
const assert = require('assert');

describe('Network-Ops Dashboard', () => {
  let browser, page;
  before(async function () {
    this.timeout(20000);
    browser = await puppeteer.launch();
    page = await browser.newPage();
    // login
    await page.goto('http://127.0.0.1:5051/login', { waitUntil: 'networkidle0' });
    await page.type('#username', 'admin');
    await page.type('#password', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForNavigation({ waitUntil: 'networkidle0' });
  });

  after(async () => {
    await browser.close();
  });

  it('shows at least one device row', async function () {
    this.timeout(15000);
    await page.goto('http://127.0.0.1:5051/genai_networks_engineer#network-ops', { waitUntil: 'networkidle0' });
    await page.waitForSelector('#network-ops-view:not(.d-none)');
    await page.waitForSelector('.device-table tbody tr', { timeout: 10000 });
    const rowCount = await page.$$eval('.device-table tbody tr', rows => rows.length);
    assert.ok(rowCount > 0);
  });
});
