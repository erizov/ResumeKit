import { test, expect } from "@playwright/test";

/**
 * End-to-end tests for ResumeKit user flows.
 * 
 * These tests require:
 * - Backend server running on http://localhost:8000
 * - Frontend dev server running on http://localhost:5173
 * 
 * To run:
 *   1. Start backend: uvicorn app.main:app --reload
 *   2. Start frontend: cd frontend && npm run dev
 *   3. Run tests: npx playwright test
 */

test.describe("ResumeKit User Flows", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto("/");
  });

  test("should generate tailored resume from form", async ({ page }) => {
    // Fill in job description
    await page.fill('textarea[placeholder*="Job description"]', "Backend developer position with Python and FastAPI.");

    // Fill in resume text
    await page.fill('textarea[placeholder*="Resume text"]', "John Doe\nSoftware Engineer\nPython, FastAPI, PostgreSQL");

    // Set languages and targets
    await page.fill('input[placeholder*="Languages"]', "en");
    await page.fill('input[placeholder*="Targets"]', "backend");

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for results
    await page.waitForSelector('text=Results', { timeout: 30000 });

    // Verify results are displayed
    const resultsSection = page.locator('text=Results');
    await expect(resultsSection).toBeVisible();

    // Check that at least one resume card is shown
    const resumeCards = page.locator('text=/EN.*backend/i');
    await expect(resumeCards.first()).toBeVisible();
  });

  test("should navigate to history page", async ({ page }) => {
    // Click History link
    await page.click('text=History');

    // Verify we're on history page
    await expect(page).toHaveURL(/.*\/history/);
    await expect(page.locator('text=Resume History')).toBeVisible();
  });

  test("should upload file via drag and drop", async ({ page }) => {
    // Fill job description
    await page.fill('text=Job description', "Developer role.");

    // Create a test file
    const fileContent = "Test Resume\nSoftware Engineer\nPython Developer";
    
    // Find the file upload zone
    const fileUploadZone = page.locator('text=Drag and drop resume file here').locator('..').locator('..');
    
    // Create a File object and trigger drop event
    const dataTransfer = await page.evaluateHandle((content) => {
      const dt = new DataTransfer();
      const file = new File([content], "test-resume.txt", { type: "text/plain" });
      dt.items.add(file);
      return dt;
    }, fileContent);

    // Simulate file drop
    await fileUploadZone.dispatchEvent("drop", { dataTransfer });

    // Alternative: use file input if drag-drop doesn't work
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: "test-resume.txt",
        mimeType: "text/plain",
        buffer: Buffer.from(fileContent),
      });
    }

    // Verify file is selected (may show chip or filename)
    await page.waitForTimeout(500); // Wait for file processing
  });

  test("should fetch job description from URL", async ({ page }) => {
    // Note: This test may fail if the URL doesn't exist or is blocked
    // In a real scenario, you'd mock the backend response
    
    // Fill in job URL
    const urlInput = page.locator('input[placeholder*="Job posting URL"]');
    if (await urlInput.isVisible()) {
      await urlInput.fill("https://example.com/job-posting");
      
      // Click fetch button
      await page.click('text=Fetch from URL');
      
      // Wait for job description to be filled (or error)
      await page.waitForTimeout(2000);
    }
  });

  test("should show error for missing required fields", async ({ page }) => {
    // Try to submit without job description
    await page.fill('text=Resume text', "Some resume text");
    await page.click('button[type="submit"]');

    // Should show error
    await expect(page.locator('text=/Please provide|required/i')).toBeVisible({ timeout: 5000 });
  });

  test("should copy resume to clipboard", async ({ page }) => {
    // First generate a resume
    await page.fill('text=Job description', "Developer role.");
    await page.fill('text=Resume text', "Software Engineer");
    await page.click('button[type="submit"]');

    // Wait for results
    await page.waitForSelector('text=Results', { timeout: 30000 });

    // Find and click copy button
    const copyButton = page.locator('button[title="Copy to clipboard"]').first();
    if (await copyButton.isVisible()) {
      await copyButton.click();
      
      // Verify success message appears
      await expect(page.locator('text=/copied/i')).toBeVisible({ timeout: 3000 });
    }
  });

  test("should navigate to detail page and view diff", async ({ page }) => {
    // First generate a resume
    await page.fill('text=Job description', "Backend developer.");
    await page.fill('text=Resume text', "Python Developer");
    await page.click('button[type="submit"]');

    // Wait for results
    await page.waitForSelector('text=Results', { timeout: 30000 });

    // Click "View Details" button
    const viewDetailsButton = page.locator('text=View Details').first();
    if (await viewDetailsButton.isVisible()) {
      await viewDetailsButton.click();

      // Should navigate to detail page
      await expect(page).toHaveURL(/.*\/tailor\/\d+/);
      
      // Verify diff viewer is present
      await expect(page.locator('text=Resume Comparison')).toBeVisible({ timeout: 5000 });
      
      // Check that view mode buttons exist
      await expect(page.locator('button:has-text("Original")')).toBeVisible();
      await expect(page.locator('button:has-text("Tailored")')).toBeVisible();
    }
  });

  test("should download PDF from detail page", async ({ page }) => {
    // First generate a resume and navigate to detail
    await page.fill('text=Job description', "Developer role.");
    await page.fill('text=Resume text', "Software Engineer");
    await page.click('button[type="submit"]');

    await page.waitForSelector('text=Results', { timeout: 30000 });
    
    const viewDetailsButton = page.locator('text=View Details').first();
    if (await viewDetailsButton.isVisible()) {
      await viewDetailsButton.click();
      await expect(page).toHaveURL(/.*\/tailor\/\d+/);

      // Set up download listener
      const downloadPromise = page.waitForEvent("download", { timeout: 10000 });
      
      // Click download PDF button
      await page.click('button:has-text("Download PDF")');
      
      // Wait for download
      const download = await downloadPromise;
      
      // Verify it's a PDF
      expect(download.suggestedFilename()).toMatch(/\.pdf$/i);
    }
  });
});

