import { test, expect } from '@playwright/test';

test.describe('Chat Widget E2E', () => {
  test('Widget opens and renders correctly on the landing page', async ({ page }) => {
    // 1. Go to the landing page
    await page.goto('/');

    // 2. Locate the chat bubble toggle (created by widget.js)
    const toggleBtn = page.locator('#alfalah-chat-toggle');
    await expect(toggleBtn).toBeVisible();

    // 3. Click the toggle to open the widget
    await toggleBtn.click();

    // 4. Verify widget UI expands
    const chatWindow = page.locator('#alfalah-chat-window');
    await expect(chatWindow).toHaveClass(/open/);

    // 5. Verify header text
    await expect(page.locator('.alfalah-chat-header-title')).toHaveText('Alfalah Investments Support');

    // 6. Verify input area exists
    await expect(page.locator('#alfalah-chat-input')).toBeVisible();
    await expect(page.locator('#alfalah-chat-send')).toBeVisible();
  });
});
