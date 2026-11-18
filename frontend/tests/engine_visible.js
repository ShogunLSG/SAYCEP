/* The skill-matching model, made visible (ADR-0025), in a real browser.
 *
 * In the journey: For you carries the model's tag; "How we matched this" opens
 * the four-step panel, whose numbers match the API and the list; the panel
 * expands to all 35 skills, traps and returns focus, and closes on Escape.
 * The Pathway says the model orders it. In the app: a job page's "How well do
 * my skills match this job?", its "Jobs with the closest skills" (with O*NET's
 * expert marks), and the CV's "Jobs your CV points to". Dark mode and 320 px.
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/engine_visible.js
 */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
let failed = 0, passed = 0;
const check = (name, ok, detail = '') => {
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  -- ' + detail : ''}`);
  ok ? passed++ : failed++;
};
const THABO = ['Operation and Control', 'Operations Monitoring', 'Equipment Maintenance', 'Active Listening', 'Critical Thinking', 'Monitoring'];

(async () => {
  const j = async (p) => (await fetch(BASE + p)).json();
  const b = await chromium.launch();
  const errs = [];
  const page = async (opts = {}) => {
    const ctx = await b.newContext({ viewport: { width: opts.width || 460, height: 900 }, colorScheme: opts.scheme || 'light' });
    const p = await ctx.newPage();
    p.on('pageerror', (e) => errs.push(e.message));
    p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    return p;
  };

  console.log('\nIn the journey: For you  (ADR-0025)');
  const p = await page();
  await p.goto(BASE);
  await p.click("text=I'm new");
  await p.click('text=Start my plan').catch(() => {});
  await p.click('text=I left school'); await p.click('.cta');
  for (const n of THABO) await p.click(`.chip[aria-label="${n}"]`);
  await p.click('.cta');
  await p.waitForSelector('.occwrap');
  check('For you carries the "Skill-matching model" tag with "How does it work?"',
    /Skill-matching model/.test(await p.textContent('.model-tag')) && (await p.locator('.model-tag button', { hasText: 'How does it work?' }).count()) === 1);
  check('every recommendation has its own "How we matched this"', (await p.locator('.occwrap .how').count()) === (await p.locator('.occwrap').count())
    && (await p.locator('.occwrap').count()) === 5);
  const rowScore = (await p.locator('.occwrap .score').nth(1).textContent()).trim();
  const rowTitle = (await p.locator('.occwrap .occ .t').nth(1).evaluate((e) => e.firstChild.textContent)).trim();
  await p.click('.occwrap .how >> nth=1');
  await p.waitForSelector('.sheet.match .mscore');
  const sheetScore = (await p.textContent('.sheet.match .mscore b')).trim();
  check('the panel opens for that job, with the same score as the list', sheetScore === rowScore
    && (await p.textContent('.sheet.match .sheet-title')).includes(rowTitle), `${rowTitle}: ${rowScore} vs ${sheetScore}`);
  const steps = await p.$$eval('.sheet.match h4.sect', (xs) => xs.map((x) => x.textContent.replace(/\s+/g, ' ').trim()));
  check('it walks the four steps, then why step 3 matters',
    ['The job, as 35 numbers', 'You, as 35 numbers', 'What makes this job different', 'The score', 'Why step 3 matters'].every((s, i) => steps[i] && steps[i].includes(s)),
    steps.join(' | '));
  const visible = await p.locator('.sheet.match .mrows').first().locator('li').count();
  await p.click('.sheet.match >> text=Show all 35 skills');
  check('it shows the top 8, and all 35 on request', visible === 8 && (await p.locator('.sheet.match .mrows').first().locator('li').count()) === 35);
  const ranges = await p.$$eval('.sheet.match .mrange-n', (xs) => xs.map((x) => x.textContent));
  check('with and without centring: two ranges, the centred one reaching below zero',
    ranges.length === 2 && /-0\.\d\d/.test(ranges[1]) && !/-0\.\d\d/.test(ranges[0]), ranges.join(' | '));
  check('every bar is decoration; its number is text (screen readers get the numbers)',
    (await p.locator('.sheet.match .mbar[aria-hidden="true"], .sheet.match .mdiv[aria-hidden="true"]').count())
      === (await p.locator('.sheet.match .mbar, .sheet.match .mdiv').count()));
  check('the panel is a labelled dialog that holds focus', (await p.getAttribute('.sheet.match', 'role')) === 'dialog'
    && /How we matched you to/.test(await p.getAttribute('.sheet.match', 'aria-label')));
  for (let i = 0; i < 6; i++) await p.keyboard.press('Tab');
  check('Tab stays inside the panel', await p.evaluate(() => !!document.activeElement.closest('.sheet.match')));
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  check('Escape closes it and focus returns to the button that opened it',
    (await p.locator('.sheet.match').count()) === 0 && await p.evaluate(() => /How we matched this/.test(document.activeElement.textContent)));
  await p.click('.model-tag button');
  await p.waitForSelector('.sheet.match .mscore');
  check('"How does it work?" opens the panel for the top recommendation',
    (await p.textContent('.sheet.match .sheet-title')).includes((await p.locator('.occwrap .occ .t').first().evaluate((e) => e.firstChild.textContent)).trim()));
  await p.click('.sheet.match .x');
  await p.click('button.occ:has-text("Gas Plant Operators")');
  await p.click('text=Aim for this job');
  await p.click('.cta'); await p.waitForSelector('.headline');
  await p.click('.cta'); await p.waitForSelector('.steps');
  check('the Pathway says the model orders its steps', /Skill-matching model\s*orders these steps/.test((await p.textContent('.pane')).replace(/\s+/g, ' ')));
  await p.context().close();

  console.log('\nIn the app: the job page, closest jobs and the CV');
  const sk = Object.fromEntries((await j('/skills')).skills.map((s) => [s.name, s.element_id]));
  const prof = await (await fetch(BASE + '/profiles', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile_type: 'school_leaver', skills: THABO.map((n) => sk[n]) }) })).json();
  await fetch(`${BASE}/profiles/${prof.profile_id}/target`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ soc_code: '47-2111.00' }) });
  const q = await page();
  await q.goto(BASE);
  await q.evaluate((id) => localStorage.setItem('saycep.plan', id), prof.profile_id);
  await q.goto(BASE);
  await q.waitForSelector('.hello');
  await q.click('.tb >> text="Explore"'); await q.click('.tabpane .tabs >> text=Search');
  await q.fill('#occ-search', 'electrician'); await q.click('.tabpane button.occ:has-text("Electricians")');
  await q.waitForSelector('#sim-h');
  const api = await j('/occupations/47-2111.00/similar');
  const shown = await q.$$eval('section.similar .occ .t', (xs) => xs.map((x) => x.firstChild.textContent.trim()));
  check('"Jobs with the closest skills": the API\'s five, in order, tagged', JSON.stringify(shown) === JSON.stringify(api.similar.map((x) => x.title))
    && /Skill-matching model/.test(await q.textContent('section.similar .model-tag')), shown.join(' | '));
  check("O*NET's expert marks match the API", (await q.locator('section.similar .expert').count()) === api.similar.filter((x) => x.expert_listed).length);
  await q.click('.how-btn');
  await q.waitForSelector('.sheet.match .mscore');
  const m = await j(`/profiles/${prof.profile_id}/match/47-2111.00`);
  check('"How well do my skills match this job?" opens the panel with the API\'s score', (await q.textContent('.sheet.match .mscore b')).trim() === m.score.toFixed(2), m.score.toFixed(2));
  await q.keyboard.press('Escape');
  await q.click('section.similar .occ >> nth=1');
  await q.waitForFunction((t) => document.querySelector('.page .sheet-title') && document.querySelectorAll('.page').length >= 1
    && [...document.querySelectorAll('.page .sheet-title')].some((h) => h.textContent === t), api.similar[1].title);
  check('a closest job opens its own page', true, api.similar[1].title);
  await q.click('.top .back'); await q.click('.top .back');
  await q.click('.tb >> text="Home"');
  await q.click('.cvcard .btn'); await q.click('text=Use an example CV');
  await q.click('.page button:has-text("Check my CV")');
  await q.waitForSelector('#cv-points');
  const pts = await q.$$eval('#cv-points ~ .list .occ .t', (xs) => xs.map((x) => x.firstChild.textContent.trim()));
  check('"Jobs your CV points to": tagged, five jobs with reasons, and says nothing is added',
    pts.length === 5 && /Skill-matching model/.test(await q.textContent('#cv-points + .model-tag'))
    && /Nothing is added to your plan/.test(await q.textContent('#cv-points ~ .note')), pts.join(' | '));
  await q.click('#cv-points ~ .list .occ >> nth=0');
  await q.waitForFunction((t) => [...document.querySelectorAll('.page .sheet-title')].some((h) => h.textContent === t), pts[0]);
  check('a job the CV points to opens its page', true, pts[0]);
  await q.context().close();

  console.log('\nScreens');
  for (const [opts, what] of [[{ scheme: 'dark' }, 'dark mode'], [{ width: 320 }, 'a 320 px phone']]) {
    const v = await page(opts);
    await v.goto(BASE);
    await v.evaluate((id) => localStorage.setItem('saycep.plan', id), prof.profile_id);
    await v.goto(BASE); await v.waitForSelector('.hello');
    await v.click('.tb >> text="Explore"'); await v.waitForSelector('.occwrap');
    await v.click('.occwrap .how >> nth=0'); await v.waitForSelector('.sheet.match .mscore');
    const box = await v.locator('.sheet.match').boundingBox();
    const wide = await v.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    check(`${what}: the panel is on screen, with no sideways scrolling`, box.y >= 0 && box.x === 0 && !wide, JSON.stringify(box));
    await v.context().close();
  }
  check('no page or console errors anywhere', errs.length === 0, errs.join(' | '));

  await b.close();
  console.log(failed ? `\n${passed} passed, ${failed} FAILED` : `\n${passed} passed. MODEL VISIBLE OK`);
  process.exitCode = failed ? 1 : 0;
})();
