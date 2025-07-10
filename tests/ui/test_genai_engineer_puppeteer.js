const puppeteer = require('puppeteer');
const { expect } = require('chai');

describe('GENAI Networks Engineer Page', function () {
    this.timeout(40000); // Extend timeout for AI agent interaction

    let browser;
    let page;

    before(async function () {
        browser = await puppeteer.launch({ headless: true });
        // Create a new incognito browser context to ensure isolation
        const context = await browser.createIncognitoBrowserContext();
        page = await context.newPage();

        // Log in before running tests
        await page.goto('http://127.0.0.1:5051/login');
        await page.type('#username', 'admin');
        await page.type('#password', 'password');
        await page.click('button[type="submit"]');
        await page.waitForNavigation();
    });

    after(async function () {
        await browser.close();
    });

    it('should load the GENAI Engineer page and allow interaction with the AI agent', async function () {
        // 1. Navigate to the GENAI Engineer page
        await page.goto('http://127.0.0.1:5051/GENAI_NETWORKS_ENGINEER');
        await page.waitForSelector('#chat-container');

        // 2. Verify UI elements are present
        const pageTitle = await page.title();
        expect(pageTitle).to.equal('GENAI Networks Engineer');
        const modeSelector = await page.$('#mode-selector');
        expect(modeSelector).to.not.be.null;

        // 3. Switch to AI Agent mode
        await page.click('a[data-mode="agent"]');
        await page.waitForSelector('#chat-input-form'); // Wait for form to be ready

        // 4. Send a message to the agent
        const initialMessageCount = (await page.$$('.message-bubble')).length;
        await page.type('#chat-input', 'List the available devices for me.');
        await page.click('#send-button');

        // 5. Wait for the agent's response
        // We expect two new messages: the user's and the agent's response
        await page.waitForFunction(
            (expectedCount) => document.querySelectorAll('.message-bubble').length >= expectedCount,
            { timeout: 35000 }, // Generous timeout for the LLM
            initialMessageCount + 2
        );

        // 6. Verify the response
        const messages = await page.$$eval('.message-bubble', bubbles => bubbles.map(b => b.textContent.trim()));
        const lastMessage = messages[messages.length - 1];
        expect(lastMessage).to.include('Here are the devices I can interact with');
    });
});
