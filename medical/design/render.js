// Render quote HTML ke PDF (A4) dan PNG. Guna: node render.js <fail.html> <output-tanpa-extension>
// Kalau kandungan terlebih satu muka surat A4, --k dikecilkan sedikit demi sedikit sampai muat.
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [src, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 3 });
  await page.goto('file://' + path.resolve(src), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const k = await page.evaluate(() => {
    const el = document.querySelector('.page');
    let k = 1;
    while (el.scrollHeight > el.clientHeight && k > 0.7) {
      k = +(k - 0.02).toFixed(2);
      document.documentElement.style.setProperty('--k', k);
    }
    return el.scrollHeight > el.clientHeight ? null : k;
  });
  if (k === null) console.error('Amaran: kandungan masih terlebih A4');
  await page.screenshot({ path: out + '.png' });
  await page.pdf({ path: out + '.pdf', format: 'A4', printBackground: true, preferCSSPageSize: true });
  await browser.close();
})();
