/* Keyboard-only walk of the demo path: Tab, Shift+Tab, Enter, Space and Escape,
 * no mouse. Checks focus order, focus traps in the sheets, focus on new
 * screens and pages, Back restoring focus, and announced results. ADR-0016.
 * Test-time only. With the server on port 8000 and Playwright on NODE_PATH:
 *   node frontend/tests/keyboard.js
 */
const { chromium } = require('playwright');
let fails = 0;
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 460, height: 860 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  const act = () => p.evaluate(() => { const a = document.activeElement;
    return { tag: a.tagName, cls: a.className && a.className.baseVal === undefined ? a.className : '', text: (a.getAttribute('aria-label') || a.textContent || '').trim().slice(0, 60),
      inDialog: !!a.closest('[role=dialog]'), inTabhost: !!a.closest('.tabhost'), visible: a.getClientRects().length > 0 }; });
  // press Tab until the focused element matches, recording everything focused on the way
  const tabTo = async (test, label, back = false, max = 120) => {
    for (let i = 0; i < max; i++) {
      await p.keyboard.press(back ? 'Shift+Tab' : 'Tab');
      const a = await act();
      if (!a.visible) { ok(false, `focus went to an invisible element (${a.tag}.${a.cls}) on the way to ${label}`); }
      if (test(a)) return a;
    }
    ok(false, `could not reach ${label} by keyboard`); return null;
  };
  const has = (s) => (a) => a.text.includes(s);
  const isCta = (a) => a.cls === 'cta';

  await p.goto('http://127.0.0.1:8000/'); await p.waitForSelector('.hero');
  await tabTo((a) => a.tag === 'INPUT', 'name field'); await p.keyboard.type('Thabo'); await p.keyboard.press('Enter');
  await p.waitForSelector('.pane .title'); await p.waitForTimeout(300);
  let a = await act(); ok(a.tag === 'H2', `journey step 1: focus on heading "${a.text}"`);
  await tabTo(has('I left school'), 'I left school'); await p.keyboard.press('Space');
  await tabTo(isCta, 'Continue'); await p.keyboard.press('Enter'); await p.waitForTimeout(400);
  a = await act(); ok(a.tag === 'H2', `step 2: focus on heading "${a.text}"`);
  for (const k of ['Operation and Control', 'Equipment Maintenance', 'Active Listening', 'Critical Thinking']) {
    await tabTo((x) => x.text === k, k); await p.keyboard.press('Space'); }
  await tabTo(isCta, 'Continue'); await p.keyboard.press('Enter'); await p.waitForSelector('.occ'); await p.waitForTimeout(300);
  a = await act(); ok(a.tag === 'H2', `step 3: focus on heading "${a.text}"`);
  await tabTo((x) => x.text === 'Search', 'Search toggle'); await p.keyboard.press('Enter');
  await tabTo((x) => x.tag === 'INPUT', 'search box'); await p.keyboard.type('electric'); await p.waitForSelector('text=Electricians');
  await p.waitForTimeout(500); ok(await p.evaluate(() => { const s = document.querySelector('.pane [role=status]'); return !!s && s.textContent.includes('match'); }), 'search result count is in a status region');
  await tabTo(has('Electricians'), 'Electricians row'); await p.keyboard.press('Enter'); await p.waitForSelector('.sheet-title');
  a = await act(); ok(a.inDialog, 'job sheet: focus moved into the dialog');
  let escaped = false;
  for (let i = 0; i < 40; i++) { await p.keyboard.press('Tab'); if (!(await act()).inDialog) escaped = true; }
  ok(!escaped, 'job sheet: 40 Tabs never leave the dialog (focus trap)');
  for (let i = 0; i < 10; i++) { await p.keyboard.press('Shift+Tab'); if (!(await act()).inDialog) escaped = true; }
  ok(!escaped, 'job sheet: Shift+Tab also stays inside');
  await p.keyboard.press('Escape'); await p.waitForTimeout(200);
  a = await act(); ok(!(await p.$('.sheet')) && a.text.includes('Electricians'), `Escape closes the sheet and focus returns to "${a.text.slice(0, 30)}"`);
  await p.keyboard.press('Enter'); await p.waitForSelector('.sheet-foot .cta');
  await tabTo(has('Aim for this job'), 'Aim for this job'); await p.keyboard.press('Enter');
  await tabTo(isCta, 'Continue'); await p.keyboard.press('Enter'); await p.waitForSelector('.headline'); await p.waitForTimeout(300);
  a = await act(); ok(a.tag === 'H2', `step 4: focus on heading "${a.text}"`);
  await tabTo(isCta, 'Continue'); await p.keyboard.press('Enter'); await p.waitForSelector('.steps'); await p.waitForTimeout(300);
  a = await act(); ok(a.tag === 'H2', `step 5: focus on heading "${a.text}"`);
  await tabTo(isCta, 'Save my plan'); await p.keyboard.press('Enter'); await p.waitForSelector('.hello'); await p.waitForTimeout(400);
  a = await act(); ok(a.cls === 'hello', `home: focus on greeting "${a.text}"`);
  // unlock card by keyboard
  await tabTo(has('Start learning'), 'Start learning'); await p.keyboard.press('Enter'); await p.waitForSelector('.ps.learning');
  await tabTo(has('I can do this now'), 'I can do this now'); await p.keyboard.press('Enter'); await p.waitForSelector('.unlock');
  a = await act(); ok(a.inDialog, 'unlock card: focus moved into the dialog');
  await p.keyboard.press('Escape'); await p.waitForTimeout(200); ok(!(await p.$('.unlock')), 'unlock card: Escape closes it');
  // pages: focus to heading, tab underneath is inert, Back restores focus
  await tabTo((x) => x.cls.startsWith('tb') && x.text === 'Explore', 'Explore tab', true); await p.keyboard.press('Enter');
  await p.waitForSelector('.tabpane .occ');
  const row = await tabTo((x) => x.cls.startsWith('occ'), 'first job row');
  await p.keyboard.press('Enter'); await p.waitForSelector('.page .sheet-title'); await p.waitForTimeout(400);
  a = await act(); ok(a.cls.includes('sheet-title'), `job page: focus on heading "${a.text}"`);
  let under = false;
  for (let i = 0; i < 60; i++) { await p.keyboard.press('Tab'); if ((await act()).inTabhost) under = true; }
  ok(!under, 'job page: 60 Tabs never reach the tab hidden underneath (inert)');
  await tabTo((x) => x.text === 'Back', 'Back'); await p.keyboard.press('Enter'); await p.waitForTimeout(300);
  a = await act(); ok(a.text === row.text, `Back returns focus to the row that opened the page ("${a.text.slice(0, 30)}")`);
  // interview practice: labelled answer box and announced feedback
  await tabTo((x) => x.text === 'Home', 'Home tab'); await p.keyboard.press('Enter');
  await tabTo(has('Start practising'), 'Start practising'); await p.keyboard.press('Enter'); await p.waitForSelector('.qtext'); await p.waitForTimeout(400);
  a = await act(); ok(a.cls.includes('qtext'), 'practice: focus on the question');
  const name = await p.evaluate(() => { const t = document.querySelector('#answer'); return document.getElementById(t.getAttribute('aria-labelledby')).textContent; });
  ok(name.length > 20, 'practice: the answer box is labelled by the question');
  await tabTo((x) => x.tag === 'TEXTAREA', 'answer box'); await p.keyboard.type('Last year at church I organised five volunteers. In the end we finished on time.');
  await tabTo(has('Get feedback'), 'Get feedback'); await p.keyboard.press('Enter'); await p.waitForSelector('.fbk');
  ok(await p.evaluate(() => !!document.querySelector('[aria-live=polite] .fbk')), 'practice: feedback appears inside a polite live region');
  // what employers ask for: Home card opens the job page at the section
  await tabTo((x) => x.text === 'Back', 'Back', true); await p.keyboard.press('Enter'); await p.waitForTimeout(300);
  await tabTo(has('See what employers ask for'), 'See what employers ask for'); await p.keyboard.press('Enter');
  await p.waitForSelector('.emp'); await p.waitForTimeout(500);
  a = await act(); ok(a.text.startsWith('What employers ask for'), `employers: focus on the section heading ("${a.text.slice(0, 30)}")`);
  console.log(errs.length ? 'PAGE ERRORS: ' + errs.join(' | ') : 'no page errors');
  console.log(fails ? `${fails} FAILED` : 'ALL PASSED');
  process.exitCode = fails || errs.length ? 1 : 0;
  await b.close();
})();
