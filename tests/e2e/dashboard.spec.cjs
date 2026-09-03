const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

function loadPlaywright() {
  const candidates = [
    process.env.PLAYWRIGHT_MODULE,
    'playwright',
    'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright',
  ].filter(Boolean);

  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (error) {
      if (error.code !== 'MODULE_NOT_FOUND') {
        throw error;
      }
    }
  }
  throw new Error('Playwright is not available. Install it with `npm install -D playwright` or set PLAYWRIGHT_MODULE.');
}

function fileExists(filePath) {
  return fs.existsSync(path.resolve(filePath));
}

const requiredMetricExports = [
  'metric_session_funnel_overall',
  'metric_session_funnel_by_month',
  'metric_session_funnel_by_brand',
  'metric_session_funnel_by_category',
  'metric_session_funnel_by_price_band',
  'metric_activity_cohort_retention',
  'metric_purchase_cohort_retention',
  'metric_rfm_segment_summary',
];

async function waitForUrl(url, timeoutMs = 60000) {
  const startedAt = Date.now();
  let lastError;
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError?.message ?? 'no response'}`);
}

async function main() {
  const python = process.env.PYTHON || 'python';
  const port = process.env.E2E_PORT || '8502';
  const baseUrl = `http://127.0.0.1:${port}`;
  const edgePath = process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';

  assert.ok(fileExists('dashboard/app.py'), 'dashboard/app.py should exist');
  for (const tableName of requiredMetricExports) {
    const exportPath = path.join('data', 'exports', tableName + '.csv');
    assert.ok(fileExists(exportPath), tableName + '.csv should exist');
  }
  const expectsCsvFallback = process.env.RETAILPULSE_DUCKDB && !fileExists(process.env.RETAILPULSE_DUCKDB);

  const server = spawn(
    python,
    ['-m', 'streamlit', 'run', 'dashboard/app.py', '--server.headless', 'true', '--server.port', port],
    { cwd: process.cwd(), stdio: ['ignore', 'pipe', 'pipe'] },
  );

  let stdout = '';
  let stderr = '';
  server.stdout.on('data', (chunk) => {
    stdout += chunk.toString();
  });
  server.stderr.on('data', (chunk) => {
    stderr += chunk.toString();
  });

  try {
    await waitForUrl(baseUrl);
    const { chromium } = loadPlaywright();
    const browser = await chromium.launch({ executablePath: edgePath, headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });

    await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 60000 });
    await page.getByText('RetailPulse', { exact: true }).waitFor({ timeout: 60000 });
    await page.getByText('Cosmetics ecommerce intelligence cockpit').waitFor({ timeout: 60000 });
    if (expectsCsvFallback) {
      await page.getByText('CSV metric exports').waitFor({ timeout: 60000 });
    }

    const kpiCards = page.locator('.rp-kpi-card');
    await kpiCards.filter({ hasText: 'Net purchase revenue' }).locator('.rp-kpi-value').filter({ hasText: '$6,351,830' }).waitFor({ timeout: 60000 });
    await kpiCards.filter({ hasText: 'Viewed sessions' }).locator('.rp-kpi-value').filter({ hasText: '4,280,701' }).waitFor({ timeout: 60000 });
    await kpiCards.filter({ hasText: 'View to cart' }).locator('.rp-kpi-value').filter({ hasText: '18.42%' }).waitFor({ timeout: 60000 });
    await page.getByText('Sales Overview').waitFor({ timeout: 60000 });
    await page.getByText('Conversion Trend').waitFor({ timeout: 60000 });

    await page.getByRole('tab', { name: 'Cohorts' }).click();
    await page.getByText('Activity Retention', { exact: true }).waitFor({ timeout: 60000 });
    await page.getByText('Purchase Retention', { exact: true }).waitFor({ timeout: 60000 });
    await page.getByText('Cohort Detail').waitFor({ timeout: 60000 });

    await page.getByRole('tab', { name: 'Segments' }).click();
    await page.getByText('Revenue by Segment').waitFor({ timeout: 60000 });
    await page.getByText('Revenue Share').waitFor({ timeout: 60000 });
    await page.getByText('Customer List').waitFor({ timeout: 60000 });
    await page.getByText('at_risk_previous_buyer').first().waitFor({ timeout: 60000 });
    await page.getByText('high_value_loyal').first().waitFor({ timeout: 60000 });

    fs.mkdirSync('test-results', { recursive: true });
    await page.screenshot({ path: 'test-results/dashboard-e2e.png', fullPage: true });
    await browser.close();

    console.log('Playwright E2E passed: dashboard overview, cohort, and segment views rendered.');
  } catch (error) {
    console.error('Playwright E2E failed.');
    console.error(error);
    if (stdout) console.error('\n--- streamlit stdout ---\n' + stdout);
    if (stderr) console.error('\n--- streamlit stderr ---\n' + stderr);
    process.exitCode = 1;
  } finally {
    server.kill('SIGTERM');
  }
}

main();
