/* A student's field of study (ADR-0029), in a real browser.
 *
 * The student's skills screen offers "What are you studying?" (optional), one
 * of O*NET's 33 knowledge areas with plain examples. The profile is created
 * with it; For you says it counts; "How we matched this" shows its share and
 * the shares still add up; the Me tab changes and clears it. A school-leaver
 * never sees the question, and the journey stays five screens (NFR-02).
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/field_of_study.js
 */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
let failed = 0, passed = 0;
const check = (name, ok, detail = '') => {
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  -- ' + detail : ''}`);
  ok ? passed++ : failed++;
};
const SKILLS = ['Programming', 'Critical Thinking', 'Mathematics', 'Complex Problem Solving'];
const COMP = '2.C.3.a';   // Computers and Electronics

(async () => {
  const b = await chromium.launch();
  const errs = [];
  const page = async (opts = {}) => {
    const ctx = await b.newContext({ viewport: { width: opts.width || 460, height: 900 }, colorScheme: opts.scheme || 'light' });
    const p = await ctx.newPage();
    p.on('pageerror', (e) => errs.push(e.message));
    p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    return p;
  };
  const posts = [];

  console.log('\nThe student journey');
  const p = await page();
  p.on('request', (r) => { if (r.method() !== 'GET' && /\/profiles/.test(r.url())) posts.push([r.method(), r.url(), r.postData()]); });
  await p.goto(BASE);
  await p.click("text=I'm new");
  await p.click('text=Start my plan').catch(() => {});
  await p.click("text=I'm studying"); await p.click('.cta');
  await p.waitForSelector('#field-select option[value="' + COMP + '"]', { state: 'attached' });
  const opts = await p.$$eval('#field-select option', (xs) => xs.map((x) => x.textContent));
  check('the skills screen asks "What are you studying?", optional, with 33 areas and a "not studying" choice',
    /What are you studying\?\s*\(optional\)/.test(await p.textContent('.fieldq label')) && opts.length === 34 && /Not studying/.test(opts[0]),
    `${opts.length} options`);
  check('each area carries plain examples', /Computers and Electronics \(IT, computer science/.test(opts.join('|')));
  check('the select has a label a screen reader announces', (await p.getAttribute('.fieldq label', 'for')) === 'field-select');
  for (const n of SKILLS) await p.click(`.chip[aria-label="${n}"]`);
  await p.selectOption('#field-select', COMP);
  check("choosing an area shows O*NET's description of it", /Computers and Electronics.*Knowledge of circuit boards/.test(await p.textContent('.fieldq .note')));
  await p.click('.cta');
  await p.waitForSelector('.tabs');
  const created = posts.find(([m, u]) => m === 'POST' && /\/profiles$/.test(u));
  check('the profile is created with the field, in the same request (no extra screen)',
    created && JSON.parse(created[2]).field_element_id === COMP, created && created[2]);
  check('still step 3 of 5 (NFR-02)', /Step\s*3\s*of 5/.test(await p.textContent('.steplabel')));
  await p.click('.tabs >> text=For you');
  await p.waitForSelector('.occwrap');
  check('For you says the field counts for a tenth', /Your field, Computers and Electronics, counts for a tenth/.test((await p.textContent('.pane')).replace(/\s+/g, ' ')));
  const rowScore = (await p.locator('.occwrap .score').first().textContent()).trim();
  await p.click('.occwrap .how >> nth=0');
  await p.waitForSelector('.sheet.match .mscore');
  const sc = (await p.textContent('.sheet.match h4.sect:has-text("The score") + p')).replace(/\s+/g, ' ');
  const nums = (sc.match(/your skills score (-?\d+\.\d+).*?at (-?\d+\.\d+).*?the match score is (-?\d+\.\d+)/) || []).slice(1).map(Number);
  check('the panel explains the field: skills score, field score, and 0.9 and 0.1 of them make the match score',
    nums.length === 3 && Math.abs(0.9 * nums[0] + 0.1 * nums[1] - nums[2]) <= 0.006 && (await p.textContent('.sheet.match .mscore b')).trim() === rowScore,
    sc.slice(0, 200));
  check('the panel text has its spaces (no "it4.87")', /rates it \d\.\d\d out of 5/.test(sc), (sc.match(/rates it.{0,12}/) || [''])[0]);
  check('"Your field" is one of the rows in what lifted or held back the score',
    (await p.locator('.sheet.match .mrows li', { hasText: 'Your field: Computers and Electronics' }).count()) === 1);
  await p.keyboard.press('Escape');
  await p.click('button.occ >> nth=0');
  await p.click('text=Aim for this job');
  await p.click('.cta'); await p.waitForSelector('.headline');
  await p.click('.cta'); await p.waitForSelector('.steps');
  check('the Pathway builds with the field', (await p.locator('.steps').count()) === 1);
  await p.click('.cta');
  await p.waitForSelector('.hello');

  console.log('\nThe Me tab');
  await p.click('.tb >> text="Me"');
  await p.waitForSelector('#me-field');
  check('Me shows the field of study, and the picker holds it',
    /Field of study\s*Computers and Electronics/.test((await p.textContent('.pane')).replace(/\s+/g, ' ')) && (await p.inputValue('#me-field')) === COMP);
  await p.selectOption('#me-field', '2.C.4.a');
  await p.waitForFunction(() => /Saved\. Your matches now include Mathematics/.test(document.querySelector('.pane').textContent));
  const pid = await p.evaluate(() => localStorage.getItem('saycep.plan'));
  const prof = await (await fetch(`${BASE}/profiles/${pid}`)).json();
  check('changing it saves straight away', prof.field && prof.field.name === 'Mathematics', JSON.stringify(prof.field));
  await p.selectOption('#me-field', '');
  await p.waitForFunction(() => /Saved: no field/.test(document.querySelector('.pane').textContent));
  const prof2 = await (await fetch(`${BASE}/profiles/${pid}`)).json();
  check('it can be cleared', prof2.field === null);
  await p.context().close();

  console.log('\nA school-leaver');
  const q = await page();
  await q.goto(BASE);
  await q.click("text=I'm new");
  await q.click('text=Start my plan').catch(() => {});
  await q.click('text=I left school'); await q.click('.cta');
  await q.waitForSelector('.chip');
  check('never sees the question', (await q.locator('#field-select').count()) === 0);
  await q.context().close();

  console.log('\nScreens');
  for (const [opts2, what] of [[{ scheme: 'dark' }, 'dark mode'], [{ width: 320 }, 'a 320 px phone']]) {
    const v = await page(opts2);
    await v.goto(BASE);
    await v.click("text=I'm new");
    await v.click('text=Start my plan').catch(() => {});
    await v.click("text=I'm studying"); await v.click('.cta');
    await v.waitForSelector('#field-select option[value="' + COMP + '"]', { state: 'attached' });
    await v.selectOption('#field-select', COMP);
    await v.waitForTimeout(600);   // let the screen's slide-in finish before measuring
    const box = await v.locator('#field-select').boundingBox();
    const wide = await v.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    check(`${what}: the picker fits, with no sideways scrolling`, box.x >= 0 && box.x + box.width <= (opts2.width || 460) && !wide, JSON.stringify(box));
    await v.context().close();
  }
  check('no page or console errors anywhere', errs.length === 0, errs.join(' | '));

  await b.close();
  console.log(failed ? `\n${passed} passed, ${failed} FAILED` : `\n${passed} passed. FIELD OF STUDY OK`);
  process.exitCode = failed ? 1 : 0;
})();
