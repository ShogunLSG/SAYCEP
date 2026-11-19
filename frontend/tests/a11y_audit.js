/* Accessibility audit (WCAG 2.1 A/AA rules) on every screen of the demo path. ADR-0016.
 *
 * Test-time only: axe-core and Playwright are never loaded by the app and are
 * not dependencies of it. With the server running on port 8000:
 *   npm i --no-save axe-core playwright      (in any scratch folder; NODE_PATH to it)
 *   node frontend/tests/a11y_audit.js                 light mode, 460 px wide
 *   SCHEME=dark node frontend/tests/a11y_audit.js     dark mode
 *   WIDTH=320 node frontend/tests/a11y_audit.js       reflow check (WCAG 1.4.10)
 * Prints one line per screen; OUT=file.json also writes every violation.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const AXE = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];
const results = [];
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: +(process.env.WIDTH || 460), height: 860 }, colorScheme: process.env.SCHEME || 'light' });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  const audit = async (name) => {
    await p.waitForTimeout(500);
    await p.evaluate(AXE);
    const r = await p.evaluate(async (tags) => {
      const res = await axe.run(document, { runOnly: { type: 'tag', values: tags } });
      return res.violations.map(v => ({ id: v.id, impact: v.impact, help: v.help,
        nodes: v.nodes.map(n => ({ t: n.target.join(' '), s: n.failureSummary.split('\n').slice(1, 2).join(' ').trim(), h: n.html.slice(0, 110) })) }));
    }, TAGS);
    const wide = await p.evaluate(() => [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed'; })
      .filter(e => !e.closest('.tabhost[inert]')).slice(0, 3).map(e => e.tagName + '.' + (e.className.baseVal ?? e.className) + ' →' + Math.round(e.getBoundingClientRect().right)));
    if (wide.length) r.push({ id: 'reflow-overflow', nodes: wide.map(t => ({ t, s: 'wider than the viewport', h: '' })) });
    results.push({ name, r });
    const n = r.reduce((a, v) => a + v.nodes.length, 0);
    console.log(`${name.padEnd(22)} ${String(r.length).padStart(2)} rules ${String(n).padStart(3)} nodes  ${r.map(v => v.id + '×' + v.nodes.length).join(', ')}`);
  };
  const cta = () => p.click('.foot .cta');
  await p.goto('http://127.0.0.1:8000/'); await p.waitForSelector('.hero'); await audit('welcome');
  await p.fill('#welcome-name', 'Thabo'); await p.click('.door .cta');
  await p.click('text=I left school'); await audit('journey 1 start'); await cta();
  for (const k of ['Operation and Control','Operations Monitoring','Equipment Maintenance','Active Listening','Critical Thinking','Monitoring'])
    await p.click(`button.chip[aria-label="${k}"]`);
  await audit('journey 2 skills'); await cta(); await p.waitForSelector('.occ'); await audit('journey 3 for you');
  await p.click('.occwrap .how >> nth=0'); await p.waitForSelector('.sheet.match .mscore'); await p.click('.sheet.match >> text=Show all 35 skills'); await audit('model panel'); await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await p.click('.tabs >> text=Search'); await p.fill('#occ-search', 'electric'); await p.waitForSelector('text=Electricians');
  await p.click('button.occ:has-text("Electricians")'); await p.waitForSelector('.sheet-title'); await audit('journey 3 job sheet');
  await p.click('.sheet-foot .cta'); await cta();
  await p.waitForSelector('.headline'); await audit('journey 4 gap'); await cta(); await p.waitForSelector('.steps'); await audit('journey 5 route');
  await cta(); await p.waitForSelector('.hello'); await audit('home');
  await p.click('.ps:has-text("Troubleshooting") >> text=Start learning'); await p.waitForSelector('.ps.learning');
  await p.click('.ps.learning >> text=I can do this now'); await p.waitForSelector('.unlock'); await audit('unlock card'); await p.click('.unlock .cta');
  await p.click('.tb >> text="Explore"'); await p.waitForSelector('.tabpane .occ'); await audit('explore for you');
  await p.click('.tabpane .tabs >> text=Search'); await p.fill('#occ-search', 'conduit installer'); await p.waitForSelector('.aka'); await audit('explore search');
  await p.click('.tabpane button.occ:has-text("Electricians")'); await p.waitForSelector('.page .sheet-title'); await p.waitForSelector('#sim-h'); await audit('job page');
  await p.click('.page-foot >> text=Save this job'); await p.waitForSelector('.page-foot >> text=Saved'); await p.click('.back');
  await p.fill('#occ-search', 'boilermakers'); await p.waitForTimeout(600); await p.click('.tabpane button.occ >> nth=0');
  await p.waitForSelector('.page .sheet-title'); await p.click('.page-foot >> text=Save this job'); await p.waitForSelector('.page-foot >> text=Saved'); await p.click('.back');
  await p.click('.tabpane .tabs >> text=Interests'); await p.waitForSelector('.qz'); await audit('interest quiz');
  const qs = p.locator('.qz'); const n = await qs.count();
  for (let i = 0; i < n; i++) { const t = await qs.nth(i).locator('p').textContent();
    await qs.nth(i).locator(`.qa:has-text("${/Fix a broken|Build or install|Check numbers/.test(t) ? "I'd enjoy it" : /Keep records|Solve a tricky/.test(t) ? 'Maybe' : 'Not for me'}")`).click(); }
  await p.click('.tabpane .cta'); await p.waitForSelector('.tabpane .fit'); await audit('quiz results');
  await p.click('.tb >> text="Skills"'); await p.waitForSelector('.skillrow'); await audit('skills tab');
  await p.click('.skillrow:has-text("Repairing")'); await p.waitForSelector('.skillstate'); await audit('skill page'); await p.click('.back');
  await p.click('.tb >> text="Home"'); await p.waitForSelector('.svd');
  await p.click('.pick >> nth=0'); await p.click('.pick >> nth=1'); await p.click('text=/Compare 2 jobs/'); await p.waitForSelector('.cmpcol'); await audit('compare'); await p.click('.back');
  await p.click('.cvcard .btn'); await p.waitForSelector('#cv-text'); await audit('cv check');
  await p.click('text=Use an example CV'); await p.click('text=Check my CV >> nth=-1');
  await p.waitForSelector('.cvs'); await p.waitForSelector('#cv-points'); await audit('cv result'); await p.click('.back');
  await p.click('text=Start practising'); await p.waitForSelector('.qtext'); await audit('practice');
  await p.fill('#answer', 'Last year at school I fixed the printer. In the end it worked.'); await p.click('text=Get feedback'); await p.waitForSelector('.fbk'); await audit('practice feedback');
  await p.fill('#answer', 'Last year at school I fixed the printer for our class. I checked the cables and replaced the toner. In the end it worked and we printed 30 pages on time, and I learned to test before and after.'); await p.click('text=Get feedback'); await p.waitForSelector('.retry'); await audit('practice retry'); await p.click('.back');
  // The advert data is optional (ADR-0017): audit the section only where it's loaded.
  if (await p.evaluate(() => fetch('/occupations/47-2111.00/adverts').then((r) => r.json()).then((d) => d.loaded))) {
    await p.click('text=See what employers ask for'); await p.waitForSelector('.emp'); await audit('employers section'); await p.click('.back');
  } else console.log('employers section      skipped: advert data not loaded');
  // Jobs for you (ADR-0022) is optional data too.
  if (await p.evaluate(() => fetch('/occupations/47-2111.00/listings').then((r) => r.json()).then((d) => d.loaded))) {
    await p.waitForSelector('.card.jobs .jc'); await p.click('.card.jobs .jc-apply >> nth=0'); await audit('jobs for you card');
    await p.click('text=/See all .* jobs for you/'); await p.waitForSelector('.page .jc'); await audit('jobs for you page'); await p.click('.back');
  } else console.log('jobs for you           skipped: listings not loaded');
  await p.click('.tb >> text="Me"'); await p.waitForSelector('#me-name'); await audit('me');
  // A student with a field of study (ADR-0029): the question, its panel row, and Me.
  await p.evaluate(() => localStorage.clear()); await p.goto('http://127.0.0.1:8000/'); await p.waitForSelector('.hero');
  await p.click('.door .cta'); await p.click("text=I'm studying"); await cta();
  for (const k of ['Programming', 'Critical Thinking', 'Mathematics']) await p.click(`button.chip[aria-label="${k}"]`);
  await p.waitForSelector('#field-select option[value="2.C.3.a"]', { state: 'attached' }); await p.selectOption('#field-select', '2.C.3.a');
  await audit('student skills + field'); await cta();
  await p.waitForSelector('.list[aria-label^="Jobs in"] .occ'); await audit('jobs in your field');
  await p.click('.tabs >> text=For you'); await p.waitForSelector('.occwrap');
  await p.click('.occwrap .how >> nth=0'); await p.waitForSelector('.sheet.match .mscore'); await audit('model panel + field');
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await p.click('button.occ >> nth=0'); await p.click('.sheet-foot .cta'); await cta(); await p.waitForSelector('.headline'); await cta();
  await p.waitForSelector('.steps'); await cta(); await p.waitForSelector('.hello');
  await p.click('.tb >> text="Me"'); await p.waitForSelector('#me-field'); await audit('me (student)');
  if (process.env.OUT) fs.writeFileSync(process.env.OUT, JSON.stringify(results, null, 1));
  const tot = results.reduce((a, s) => a + s.r.reduce((b, v) => b + v.nodes.length, 0), 0);
  console.log('TOTAL failing elements', tot, '·', errs.length ? 'PAGE ERRORS: ' + errs.join(' | ') : 'no page errors');
  process.exitCode = tot || errs.length ? 1 : 0;
  await b.close();
})();
