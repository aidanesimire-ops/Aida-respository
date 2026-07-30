// Render the print-styled HTML reports to PDF via headless Chromium (Playwright).
//   node analysis/render_pdf.cjs
// Renders:
//   outputs/neighborhood_reports.html        -> outputs/Neighborhood_System_Reports.pdf  (combined book)
//   outputs/neighborhoods/<slug>.html         -> outputs/neighborhoods/<slug>.pdf          (one per neighborhood)
const fs = require('fs');
const path = require('path');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'outputs');
const INDIV = path.join(OUT, 'neighborhoods');

const PDF_OPTS = {
  format: 'Letter', printBackground: true,
  margin: { top: '0', bottom: '0', left: '0', right: '0' },
};

async function render(page, srcAbs, outAbs) {
  await page.goto('file://' + srcAbs, { waitUntil: 'networkidle' });
  await page.pdf({ path: outAbs, ...PDF_OPTS });
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // combined book
  await render(page, path.join(OUT, 'neighborhood_reports.html'),
               path.join(OUT, 'Neighborhood_System_Reports.pdf'));
  console.log('Wrote outputs/Neighborhood_System_Reports.pdf');

  // individual one-pagers
  let n = 0;
  if (fs.existsSync(INDIV)) {
    const files = fs.readdirSync(INDIV).filter(f => f.endsWith('.html')).sort();
    for (const f of files) {
      const out = path.join(INDIV, f.replace(/\.html$/, '.pdf'));
      await render(page, path.join(INDIV, f), out);
      n++;
    }
  }
  console.log(`Wrote ${n} individual PDFs in outputs/neighborhoods/`);
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
