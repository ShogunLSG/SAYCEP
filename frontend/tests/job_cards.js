/* Jobs for you (ADR-0022): the job cards, in a real browser.
 *
 * Checks the Home card, the Jobs page and the job-page section against the
 * API: labelling, ranking, fit counts, Apply, links, show more, live updates
 * when a skill or the goal changes, a job with no listings, the enrolled
 * student, the keyboard, dark mode and a 320 px screen.
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/job_cards.js
 */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
const ELECTRICIANS = '47-2111.00', PLUMBERS = '47-2152.00', NO_LISTINGS = '13-1041.06';   // Coroners: no linked adverts
let failed = 0, passed = 0;
const check = (name, ok, detail = '') => {
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  -- ' + detail : ''}`);
  ok ? passed++ : failed++;
};
const THABO = ['Operation and Control', 'Operations Monitoring', 'Equipment Maintenance', 'Active Listening', 'Critical Thinking', 'Monitoring'];

(async () => {
  const j = async (p, o) => (await fetch(BASE + p, o)).json();
  const send = (method, p, body) => fetch(BASE + p, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const sk = Object.fromEntries((await j('/skills')).skills.map((s) => [s.name, s.element_id]));
  const make = async (type, goal) => {
    const pr = await j('/profiles', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_type: type, skills: THABO.map((n) => sk[n]) }) });
    await send('PUT', `/profiles/${pr.profile_id}/target`, { soc_code: goal });
    return pr.profile_id;
  };

  const b = await chromium.launch();
  const errs = [];
  const open = async (pid, opts = {}) => {
    const ctx = await b.newContext({ viewport: { width: opts.width || 460, height: 900 }, colorScheme: opts.scheme || 'light' });
    const p = await ctx.newPage();
    p.on('pageerror', (e) => errs.push(e.message));
    p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(BASE);
    await p.evaluate((id) => localStorage.setItem('saycep.plan', id), pid);
    await p.goto(BASE);
    await p.waitForSelector('.hello');
    return p;
  };
  const homeCards = (p) => p.locator('section.card.jobs .jc');
  const haveOf = async (card) => (await card.locator('.jc-have b').textContent()).match(/(\d+) of the (\d+)/).slice(1).map(Number);

  const pid = await make('school_leaver', ELECTRICIANS);
  const api = await j(`/profiles/${pid}/listings?limit=40`);
  const p = await open(pid);

  console.log('\nJobs for you on Home  (ADR-0022)');
  await p.waitForSelector('section.card.jobs .jc');
  check('three cards, best fit first', (await homeCards(p).count()) === 3);
  const badge = await p.textContent('section.card.jobs .sample');
  check('labelled every time: sample listings, US, demo data, closed, not openings',
    ['Sample listings', 'United States', 'demo data', 'closed', 'not openings'].every((w) => badge.includes(w)), badge.trim());
  const titles = await p.$$eval('section.card.jobs .jc-t', (xs) => xs.map((x) => x.textContent));
  check('the order is the API ranking', JSON.stringify(titles) === JSON.stringify(api.listings.slice(0, 3).map((x) => x.title)), titles.join(' | '));
  const [h0, m0] = await haveOf(homeCards(p).first());
  check('fit counts are the API counts', h0 === api.listings[0].fit.have && m0 === api.listings[0].fit.mentioned, `${h0} of ${m0}`);
  check('each card has a fit word, a date, a place and a progress bar',
    (await p.locator('section.card.jobs .fitb').count()) === 3 && (await p.locator('section.card.jobs .jc-when').count()) === 3
    && (await p.locator('section.card.jobs [role=progressbar]').count()) === 3);
  check('no company, link or pay on any card',
    !/(\$|salary|https?:|www\.)/i.test(await p.textContent('section.card.jobs')));
  check('"See all" gives the true total', (await p.textContent('section.card.jobs .btn.full')).includes(`See all ${api.total} jobs`));

  console.log('\nApply');
  const apply = homeCards(p).first().locator('.jc-apply');
  const note = homeCards(p).first().locator('.jc-note');
  check('closed by default', (await apply.getAttribute('aria-expanded')) === 'false' && !(await note.isVisible()));
  await apply.click();
  check('opens a note that says it is a demo listing', (await apply.getAttribute('aria-expanded')) === 'true'
    && (await note.isVisible()) && /demo listing/.test(await note.textContent()));
  await apply.focus(); await p.keyboard.press('Enter');
  check('the keyboard closes it again (Enter)', (await apply.getAttribute('aria-expanded')) === 'false');
  check('the note is tied to its button (aria-controls)', (await apply.getAttribute('aria-controls')) === (await note.getAttribute('id')));

  console.log('\nThe Jobs page');
  await p.click('section.card.jobs .btn.full');
  await p.waitForSelector('.page .jc');
  check('it lists every listing for the goal and the route', (await p.locator('.page .jc').count()) === Math.min(api.total, 40),
    `${await p.locator('.page .jc').count()} of ${api.total}`);
  const pageOcc = await p.$$eval('.page .jc-meta .tl', (xs) => [...new Set(xs.map((x) => x.textContent))]);
  check('cards come from the goal and the jobs on the route', pageOcc.length >= 2, pageOcc.join(' | '));
  await p.click('.top .back');
  await p.waitForSelector('section.card.jobs');
  check('Back returns to Home, and focus to the button that opened it',
    await p.evaluate(() => document.activeElement && /See all/.test(document.activeElement.textContent)));

  console.log('\nFrom a card to its job, and the job page section');
  const occ = await homeCards(p).first().locator('.jc-meta .tl').textContent();
  await homeCards(p).first().locator('.jc-meta .tl').click();
  await p.waitForSelector('.page .sheet-title');
  check('the job link on a card opens that job', (await p.textContent('.page .sheet-title')) === occ, occ);
  await p.click('.top .back');
  await p.waitForSelector('section.card.jobs');
  await p.click('.tb >> text="Explore"');
  await p.click('.tabpane .tabs >> text=Search');
  await p.fill('#occ-search', 'electrician');
  await p.click('.tabpane button.occ:has-text("Electricians")');
  await p.waitForSelector('#jl-h');
  const sec = p.locator('section[aria-labelledby="jl-h"]');
  check('a job page has its own sample listings, labelled', (await sec.locator('.jc').count()) === 3
    && /Sample listings/.test(await sec.locator('.sample').textContent()));
  await sec.locator('button.more').click();
  const all = await sec.locator('.jc').count();
  check('"Show more" shows the rest (up to 10)', all > 3 && all <= 10, `${all}`);
  await sec.locator('button.more').click();
  check('"Show fewer" goes back to three', (await sec.locator('.jc').count()) === 3);
  check('job-page cards are all for this job', (await sec.locator('.jc-meta .tl').count()) === 0);

  console.log('\nLive updates');
  await p.click('.tb >> text="Home"');
  await p.waitForSelector('section.card.jobs .jc');
  // In the app, without a reload: "I can do this now" on Home, as in demo step 6.
  const before = JSON.stringify(await p.$$eval('section.card.jobs .jc-have', (xs) => xs.map((x) => x.textContent)));
  await p.click('.ps:has-text("Troubleshooting") >> text=Start learning');
  await p.click('.ps.learning:has-text("Troubleshooting") >> text=I can do this now');
  await p.waitForSelector('.unlock', { timeout: 5000 }).then(() => p.click('.unlock .cta')).catch(() => {});
  await p.waitForTimeout(2500);   // let every refetch land, then compare with the API
  const live = (await j(`/profiles/${pid}/listings?limit=3`)).listings.map((x) => `${x.fit.have} of the ${x.fit.mentioned}`);
  const shown = await p.$$eval('section.card.jobs .jc-have b', (xs) => xs.map((x) => x.textContent));
  check('"I can do this now" on Home updates the cards straight away, with no reload',
    JSON.stringify(shown) === JSON.stringify(live) && JSON.stringify(shown) !== before, `ui ${shown.join(' / ')} vs api ${live.join(' / ')}`);
  const first = (await j(`/profiles/${pid}/listings?limit=1`)).listings[0];
  const toLearn = first.skills.find((k) => !k.status);
  await send('PUT', `/profiles/${pid}/skills/${toLearn.element_id}`, { status: 'held' });
  await p.click('.tb >> text="Skills"'); await p.click('.tb >> text="Home"');   // a tab switch re-reads the plan
  await p.reload(); await p.waitForSelector('section.card.jobs .jc');
  const afterAll = (await j(`/profiles/${pid}/listings?limit=40`)).listings;
  const same = (await j(`/occupations/${first.soc_code}/listings?profile_id=${pid}&limit=20`)).listings
    .find((x) => x.advert_id === first.advert_id);
  const [h1, m1] = await haveOf(homeCards(p).first());
  check('marking a skill held raises that advert\'s fit by one, and Home shows the new ranking',
    same && same.fit.have === first.fit.have + 1 && h1 === afterAll[0].fit.have && m1 === afterAll[0].fit.mentioned,
    `${toLearn.name}: ${first.fit.have} -> ${same && same.fit.have}; top card ${h1} of ${m1}`);
  await send('PUT', `/profiles/${pid}/target`, { soc_code: PLUMBERS });
  await p.reload(); await p.waitForSelector('section.card.jobs .jc');
  const route = (await j(`/profiles/${pid}/pathway`)).steps.map((s) => s.title);
  const now = await p.$$eval('section.card.jobs .jc-meta .tl', (xs) => xs.map((x) => x.textContent));
  check('a new goal brings listings for the new goal and its route', now.every((o) => route.includes(o)), now.join(' | '));
  await p.context().close();

  console.log('\nOther users and states');
  const none = await make('school_leaver', NO_LISTINGS);
  const q = await open(none);
  await q.waitForTimeout(800);
  const noneApi = await j(`/profiles/${none}/listings`);
  check('a goal with no adverts of its own: Home shows only its route\'s listings, or nothing',
    noneApi.listings.every((x) => x.soc_code !== NO_LISTINGS)
    && ((await q.locator('section.card.jobs').count()) === (noneApi.listings.length ? 1 : 0)), `${noneApi.total} listings`);
  await q.click('.tb >> text="Explore"'); await q.click('.tabpane .tabs >> text=Search');
  await q.fill('#occ-search', 'coroner'); await q.click('.tabpane button.occ:has-text("Coroners")');
  await q.waitForSelector('.page .sheet-title'); await q.waitForTimeout(800);
  check('a job with no adverts has no listings section, and no error', (await q.locator('#jl-h').count()) === 0);
  await q.context().close();
  const stu = await make('student', ELECTRICIANS);
  const s = await open(stu);
  await s.waitForSelector('section.card.jobs .jc');
  check('the enrolled student gets job cards too', (await s.locator('section.card.jobs .jc').count()) === 3);
  await s.context().close();

  console.log('\nScreens');
  for (const [opts, what] of [[{ scheme: 'dark' }, 'dark mode'], [{ width: 320 }, 'a 320 px phone']]) {
    const v = await open(pid, opts);
    await v.waitForSelector('section.card.jobs .jc');
    const wide = await v.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    const fg = await v.$eval('section.card.jobs .jc-t', (e) => getComputedStyle(e).color);
    const bg = await v.$eval('section.card.jobs .jc', (e) => getComputedStyle(e).backgroundColor);
    check(`${what}: no sideways scrolling, and the card text is not the background colour`, !wide && fg !== bg, `${fg} on ${bg}`);
    await v.context().close();
  }
  check('no page or console errors anywhere', errs.length === 0, errs.join(' | '));

  await b.close();
  console.log(failed ? `\n${passed} passed, ${failed} FAILED` : `\n${passed} passed. JOB CARDS OK`);
  process.exitCode = failed ? 1 : 0;
})();
