// Render the print-styled HTML reports to PDF via headless Chromium (Playwright).
//   node analysis/render_pdf.cjs
// Renders outputs/neighborhood_reports.html -> outputs/Neighborhood_System_Reports.pdf
const path = require('path');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const ROOT = path.resolve(__dirname, '..');
const JOBS = [
  ['outputs/neighborhood_reports.html', 'outputs/Neighborhood_System_Reports.pdf'],
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const [src, out] of JOBS) {
    const url = 'file://' + path.join(ROOT, src);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.pdf({
      path: path.join(ROOT, out),
      format: 'Letter',
      printBackground: true,
      margin: { top: '0', bottom: '0', left: '0', right: '0' },
    });
    console.log('Wrote', out);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
