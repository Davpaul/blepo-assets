// Print manual.html to ../belt-cnc-build-guide.pdf at true size (A4, 100%).
//   node make_pdf.js
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(__dirname, 'manual.html'), { waitUntil: 'load' });
  await page.pdf({
    path: path.resolve(__dirname, '..', 'belt-cnc-build-guide.pdf'), format: 'A4', printBackground: true, preferCSSPageSize: true, scale: 1,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font-size:7px;color:#6b7280;padding:0 13mm;display:flex;justify-content:space-between;font-family:Helvetica,Arial,sans-serif"><span>Belt CNC build guide. Print at 100% (actual size): hardware drawings are life size.</span><span>page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>',
  });
  await browser.close();
  console.log('wrote belt-cnc-build-guide.pdf');
})();
