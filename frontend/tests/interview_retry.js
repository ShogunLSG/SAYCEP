/* Interview retry, the technical question and CV advice (ADR-0024), in a real browser.
 *
 * Walks the interview practice for Electricians: the technical question comes
 * after the skill questions; a weak answer then a better one shows "n of 7 ->
 * m of 7" with what is now there; sentence starters show only for the missing
 * parts; the checklist reads out for a screen reader. Then the CV page: the
 * "What to add" advice appears, labelled, and a CV that already says it gets
 * less of it. Nothing is ever stored.
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/interview_retry.js
 */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
let failed = 0, passed = 0;
const check = (name, ok, detail = '') => {
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  -- ' + detail : ''}`);
  ok ? passed++ : failed++;
};
const THABO = ['Operation and Control', 'Operations Monitoring', 'Equipment Maintenance', 'Active Listening', 'Critical Thinking', 'Monitoring'];
const WEAK = 'I fixed it.';
const STRONG = 'Last year at school I tracked the stock list for our robotics club. I made a sheet in Microsoft Excel with every part and its count. '
  + 'I checked it every Friday and told the teacher when parts ran low. In the end we never ran out before a competition, and I learned to keep records.';

(async () => {
  const j = async (p, o) => (await fetch(BASE + p, o)).json();
  const sk = Object.fromEntries((await j('/skills')).skills.map((s) => [s.name, s.element_id]));
  const pr = await j('/profiles', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile_type: 'school_leaver', skills: THABO.map((n) => sk[n]) }) });
  await fetch(`${BASE}/profiles/${pr.profile_id}/target`, { method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ soc_code: '47-2111.00' }) });

  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 460, height: 1000 } });
  const errs = [], posted = [];
  p.on('pageerror', (e) => errs.push(e.message));
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('request', (r) => { if (r.method() !== 'GET') posted.push(r.url().replace(BASE, '')); });
  await p.goto(BASE);
  await p.evaluate((id) => localStorage.setItem('saycep.plan', id), pr.profile_id);
  await p.goto(BASE);
  await p.waitForSelector('.hello');

  console.log('\nInterview practice  (ADR-0024)');
  await p.click('text=Start practising');
  await p.waitForSelector('.qtext');
  const dots = await p.locator('.qdot').count();
  check('five questions: opener, two skills, a tool, a task', dots === 5, `${dots}`);
  await p.click('.qdot >> nth=3');
  const qt = await p.textContent('.qtext');
  check('question 4 is the technical one, about a tool the adverts name', /Microsoft Excel/.test(qt), qt);
  check('the screen says it is a technical question about a tool or software the job uses',
    /technical question about\s*Microsoft Excel/.test((await p.textContent('.page-body')).replace(/\s+/g, ' ')));

  await p.fill('#answer', WEAK);
  await p.click('text=Get feedback');
  await p.waitForSelector('.fbk .big-count');
  const first = await p.textContent('.fbk .big-count');
  check('a first check shows a count and no comparison yet', /\d of 7/.test(first) && (await p.locator('.retry').count()) === 0, first.trim());
  const starters = await p.textContent('.starters');
  check('sentence starters appear for the missing parts of the story',
    /Situation/.test(starters) && /Result/.test(starters), starters.replace(/\s+/g, ' ').slice(0, 90));
  const firstMet = +(await p.textContent('.fbk .big-count b'));
  const tipTool = await p.locator('.fbk li', { hasText: 'Names Microsoft Excel' }).textContent();
  check('the tool item is there and not yet met', /Names Microsoft Excel/.test(tipTool) && /Say which tool/.test(tipTool));

  await p.fill('#answer', STRONG);
  await p.click('text=Get feedback');
  await p.waitForSelector('.retry');
  const retry = (await p.textContent('.retry')).replace(/\s+/g, ' ');
  const nowMet = +(await p.textContent('.fbk .big-count b'));
  check('checking again shows "n of 7 → m of 7" with the gain', new RegExp(`${firstMet} of 7.*${nowMet} of 7`).test(retry) && nowMet > firstMet, retry);
  check('it says what is now there', /Now there:/.test(retry) && /Names Microsoft Excel/.test(retry), retry);
  check('a screen reader gets words, not just an arrow ("then")', (await p.locator('.retry .sr-only').count()) === 1);
  check('a good answer: all seven met, no sentence starters left', nowMet === 7 && (await p.locator('.starters').count()) === 0, `${nowMet} of 7`);

  await p.click('text=Get feedback');
  await p.waitForFunction(() => /no change/.test(document.querySelector('.retry')?.textContent || ''));
  check('checking the same answer again says no change', /no change/.test(await p.textContent('.retry')));

  await p.click('.qdot >> nth=1');
  await p.fill('#answer', WEAK);
  await p.click('text=Get feedback');
  await p.waitForSelector('.fbk .big-count');
  check('each question keeps its own history: question 2 starts fresh', (await p.locator('.retry').count()) === 0);
  check('the feedback call sends only the answer, the skill or the tool; nothing is stored',
    posted.every((u) => u === '/interview/feedback') && posted.length === 4, JSON.stringify(posted));
  await p.click('.back');

  console.log('\nCV advice  (ADR-0024)');
  await p.click('.cvcard .btn');
  await p.waitForSelector('#cv-text');
  await p.fill('#cv-text', 'Lerato Nkosi. Matric 2023. Shop assistant at Pick n Pay: served customers at the till, kept stock records. Volunteer: replaced plugs in the community hall.');
  await p.click('.page button:has-text("Check my CV")');
  await p.waitForSelector('#cv-add');
  const adviceItems = await p.$$eval('.addtip', (xs) => xs.map((x) => x.textContent.replace(/\s+/g, ' ')));
  const parts = await p.$$eval('.addtip', (xs) => xs.map((x) => [x.querySelector('b').textContent, x.querySelector('.addwhy').textContent, x.querySelector('.quote').textContent]));
  check('"What to add" lists advice for the goal, each with a title, a reason and an example',
    parts.length >= 3 && parts.every((x) => x.every((s) => s.trim().length > 10 || x[0] === s)), `${parts.length} items: ${parts.map((x) => x[0]).join(', ')}`);
  check('requirements say how many US adverts and when',
    adviceItems.some((t) => /of the 84 US adverts for this job \(April 2024\)/.test(t)));
  check('the section says to add only what is true, and that the figures are US', /Only add what is true/.test(await p.textContent('#cv-add + .note')) && /United States/.test(await p.textContent('#cv-add + .note')));
  const before = adviceItems.length;
  await p.fill('#cv-text', (await p.inputValue('#cv-text')) + ' I hold a trade certificate and a Code 8 driver\'s licence.');
  await p.click('.page button:has-text("Check my CV")');
  await p.waitForFunction((n) => document.querySelectorAll('.addtip').length < n, before, { timeout: 5000 }).catch(() => {});
  const after = await p.$$eval('.addtip', (xs) => xs.map((x) => x.textContent));
  check('a CV that already names a licence gets less advice, and no licence advice',
    after.length < before && !after.some((t) => /trade licence or certificate|driver's licence/.test(t)), `${before} -> ${after.length}`);
  check('no page or console errors', errs.length === 0, errs.join(' | '));

  await b.close();
  console.log(failed ? `\n${passed} passed, ${failed} FAILED` : `\n${passed} passed. INTERVIEW AND CV ADVICE OK`);
  process.exitCode = failed ? 1 : 0;
})();
