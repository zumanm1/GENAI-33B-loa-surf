const puppeteer = require('puppeteer');
const assert = require('assert');
const fs = require('fs');
const path = require('path');

describe('Documents Upload', () => {
  let browser;
  let page;
  const testFilePath = path.join(__dirname, 'testdoc.txt');

  before(async function () {
    this.timeout(15000);
    // create temp test file
    fs.writeFileSync(testFilePath, 'Hello RAG');

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
    if (fs.existsSync(testFilePath)) fs.unlinkSync(testFilePath);
    await browser.close();
  });

  it('should upload a document and list it', async function () {
    this.timeout(15000);
    // go to documents view
    await page.goto('http://127.0.0.1:5051/genai_networks_engineer#documents', { waitUntil: 'networkidle0' });
    await page.waitForSelector('#documents-view:not(.d-none)');

    // attach file to hidden input
    await page.setInputFiles('#doc-upload-input', testFilePath);

    // wait until it appears in list
    await page.waitForFunction(
      (filename) => {
        const items = Array.from(document.querySelectorAll('.doc-item')).map(el => el.textContent.trim());
        return items.includes(filename);
      },
      { timeout: 10000 },
      'testdoc.txt'
    );

    const listed = await page.$$eval('.doc-item', els => els.map(e => e.textContent.trim()));
    assert.ok(listed.includes('testdoc.txt'));
  });
});
