import { test, expect } from '@playwright/test';

test.describe('Chat Widget E2E', () => {
  test('Widget opens and renders correctly on the landing page', async ({ page }) => {
    // 1. Go to the landing page
    await page.goto('/');

    // 2. Locate the chat bubble toggle (created by widget.js)
    const toggleBtn = page.locator('#alf-launcher');
    await expect(toggleBtn).toBeVisible();

    // 3. Click the toggle to open the widget
    await toggleBtn.click();

    // 4. Verify widget UI expands (alf-hidden class removed)
    const chatWindow = page.locator('#alf-window');
    await expect(chatWindow).not.toHaveClass(/alf-hidden/);

    // 5. Verify header text
    await expect(page.locator('#alf-header-title')).toHaveText('Alfalah GPT');

    // 6. Verify input area exists
    await expect(page.locator('#alf-input')).toBeVisible();
    await expect(page.locator('#alf-send')).toBeVisible();
  });
});
