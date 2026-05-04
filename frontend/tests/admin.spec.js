import { test, expect } from '@playwright/test';

test.describe('Admin SPA E2E', () => {
  test('Login redirects to dashboard and saves JWT', async ({ page }) => {
    // 1. Go to login page
    await page.goto('/admin/login');

    // 2. We mock the API endpoint since the backend isn't running in this frontend-only test phase
    await page.route('/api/v1/auth/token', async route => {
      const json = { access_token: 'fake-jwt-token', token_type: 'bearer' };
      await route.fulfill({ json });
    });

    // 3. Fill the form
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // 4. Expect redirection to dashboard
    await page.waitForURL('**/admin/dashboard');
    expect(page.url()).toContain('/admin/dashboard');

    // 5. Verify local storage has the token
    const token = await page.evaluate(() => localStorage.getItem('alf_admin_token'));
    expect(token).toBe('fake-jwt-token');
  });

  test('Dashboard loads layout correctly', async ({ page }) => {
    // Inject token to bypass auth check
    await page.addInitScript(() => {
      localStorage.setItem('alf_admin_token', 'fake-token');
    });

    // Mock the stats endpoint
    await page.route('/api/v1/admin/stats', async route => {
      await route.fulfill({ json: {
        total_conversations: 42,
        open_tickets: 5,
        total_documents: 10,
        active_model: 'gpt-4o-mini',
        active_prompt: 'System prompt content'
      }});
    });

    await page.goto('/admin/dashboard');

    // Verify layout injection
    await expect(page.locator('.sidebar-brand')).toBeVisible();
    await expect(page.locator('.page-title')).toHaveText('Dashboard');

    // Verify stats injected into DOM
    await expect(page.locator('text=42')).toBeVisible();
    await expect(page.locator('text=gpt-4o-mini')).toBeVisible();
  });
});
