const puppeteer = require('puppeteer');
const assert = require('assert');

describe('Chat Functionality', () => {
    let browser;
    let page;

    before(async function() {
        this.timeout(15000);
        browser = await puppeteer.launch();
        page = await browser.newPage();

        // Login before running tests
        await page.goto('http://127.0.0.1:5051/login', { waitUntil: 'networkidle0' });
        await page.type('#username', 'admin');
        await page.type('#password', 'admin');
        await page.click('button[type="submit"]');
        await page.waitForNavigation({ waitUntil: 'networkidle0' });
    });

    after(async () => {
        await browser.close();
    });

    it('should send a message and display the conversation', async () => {
        assert.strictEqual(page.url(), 'http://127.0.0.1:5051/', 'Should be on the root page after login');

        // Navigate to the chat view
        await page.goto('http://127.0.0.1:5051/genai_networks_engineer#chat', { waitUntil: 'networkidle0' });

        // Wait for the chat view to be visible
        await page.waitForSelector('#chat-view:not(.d-none)', { timeout: 5000 });

        // Type a message into the chat input
        const testMessage = 'Hello, AI!';
        await page.type('#chat-input-full', testMessage);

        // Use a robust selector to find the 'Send' button and click it
        const sendButton = await page.waitForXPath("//div[contains(@class, 'chat-input-area')]//button[contains(., 'Send')]");
        assert.ok(sendButton, 'Send button should be found');
        await sendButton.click();

        // Wait for both user and AI messages to appear
        await page.waitForSelector('.user-message');
        await page.waitForSelector('.ai-message');

        // Verify messages
        const userMessage = await page.$eval('.user-message', el => el.textContent);
        const aiMessage = await page.$eval('.ai-message', el => el.textContent);

        assert.strictEqual(userMessage, testMessage, 'User message should be correct.');
        assert.ok(aiMessage.length > 0, 'AI should provide a response.');
    }).timeout(10000);
});
