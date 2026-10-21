/* The presentation demo, run by machine: docs/presentation.md §3, step by step.
 *
 * Follows the 15 steps of the demo script in a real browser and checks the
 * numbers the script says out loud. If one of them drifts (after a data
 * rebuild, a code change, a different checkout), this fails on that step and
 * says which. Run it before every rehearsal and on the presenting laptop.
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/demo_walk.js
 *   SHOTS=/some/folder node frontend/tests/demo_walk.js     also saves a screenshot per step
 *   BASE=http://127.0.0.1:8001 node frontend/tests/demo_walk.js   another address or port
 *   SHORT=1 node frontend/tests/demo_walk.js                       the 7-minute path only
 * Exit code 0 only if every check passed and the page logged no errors.
 */
const { chromium } = require('playwright');
const SHOTS = process.env.SHOTS;
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
const SHORT = !!process.env.SHORT;      // the 7-minute path: docs/presentation.md §3 (skips steps 7-10)
let fails = 0, step = '';
const say = (m) => console.log(m);
const ok = (c, m, got) => { say(`  ${c ? 'PASS' : 'FAIL'}  ${m}${c ? '' : `   (got: ${String(got).replace(/\s+/g, ' ').slice(0, 160)})`}`); if (!c) fails++; };
const has = (text, ...parts) => parts.every((x) => (x instanceof RegExp ? x.test(text) : text.includes(x)));

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 460, height: 860 } });
  const p = await ctx.newPage();
  const errs = [];
  p.on('pageerror', (e) => errs.push(e.message));
  p.on('console', (m) => m.type() === 'error' && !/CERT|fonts/.test(m.text()) && errs.push(m.text()));
  const txt = (sel) => p.textContent(sel).then((t) => (t || '').replace(/\s+/g, ' ').trim());
  const shot = async (n) => { if (SHOTS) { await p.waitForTimeout(500); await p.screenshot({ path: `${SHOTS}/${n}.png` }); } };
  const head = (n, t) => { step = n; say(`\nStep ${n}  ${t}`); };
  const cta = () => p.click('.foot .cta');

  head(1, 'Welcome: a first name, no email or password');
  await p.goto(BASE + '/'); await p.waitForSelector('.hero');
  const hero = await txt('.hero');
  ok(has(hero, 'Find a career you can actually reach'), 'welcome screen shows the headline', hero);
  ok(has(await txt('.door'), /plan code/i) && has(await txt('.door'), /no email/i), 'the door says "No email, no password" and offers a plan code', await txt('.door'));
  await p.fill('#welcome-name', 'Thabo'); await shot('01-welcome'); await p.click('.door .cta');

  head(2, 'I left school, tick the six operator skills');
  await p.click('text=I left school'); await cta();
  for (const k of ['Operation and Control', 'Operations Monitoring', 'Equipment Maintenance', 'Active Listening', 'Critical Thinking', 'Monitoring'])
    await p.click(`button.chip[aria-label="${k}"]`);
  ok((await p.locator('button.chip[aria-pressed="true"]').count()) === 6, 'six skills ticked', await p.locator('button.chip[aria-pressed="true"]').count());
  await shot('02-skills'); await cta(); await p.waitForSelector('.occ');

  head(3, 'For you: ranked, with why; Search "electric"; Electricians; Aim for this job');
  const forYou = await txt('.pane');
  ok(has(forYou, 'Because you have'), 'each recommendation says why ("Because you have…")', forYou);
  await shot('03-for-you');
  await p.click('.tabs >> text=Search'); await p.fill('#occ-search', 'electric'); await p.waitForSelector('text=Electricians');
  await p.click('button.occ:has-text("Electricians")'); await p.waitForSelector('.sheet-title');
  const sheet = await txt('.sheet');
  ok(has(sheet, 'Electricians', 'A day in this job'), 'job panel shows the job and "A day in this job"', sheet);
  await shot('03b-electricians'); await p.click('.sheet-foot .cta'); await cta();

  head(4, 'The gap: 6 of 34 held, 2 must-haves (Troubleshooting, Repairing)');
  await p.waitForSelector('.headline');
  const gap = await txt('.pane');
  ok(has(gap, /6 of the 34/), '"6 of the 34" skills already held', gap);
  ok(has(gap, /2 must-haves?/i) || has(gap, 'Troubleshooting', 'Repairing'), 'two must-haves named', gap);
  ok(has(gap, 'Troubleshooting') && has(gap, 'Repairing'), 'Troubleshooting and Repairing are the must-haves', gap);
  await shot('04-gap'); await cta(); await p.waitForSelector('.steps');

  head(5, 'The route: four jobs, each saying why; Save as my plan');
  const route = await txt('.steps');
  const order = ['Boilermakers', 'Power-Line Installers', 'Electronics Repairers', 'Electricians'].map((t) => route.indexOf(t));
  ok(order.every((i) => i >= 0) && order.every((i, k) => k === 0 || i > order[k - 1]),
     'route order: Boilermakers → Power-Line Installers → Electronics Repairers → Electricians', route);
  ok(has(route, /Closest to you now/), 'steps say why ("Closest to you now…")', route);
  await shot('05-route'); await cta(); await p.waitForSelector('.hello');

  head(6, 'Home: learning changes nothing; "I can do this now" opens the unlock card');
  ok(has(await txt('.hello'), 'Thabo'), 'Home greets by name');
  await p.click('.ps:has-text("Troubleshooting") >> text=Start learning'); await p.waitForSelector('.ps.learning');
  ok(true, 'Start learning marks it learning');
  await p.click('.ps.learning >> text=I can do this now'); await p.waitForSelector('.unlock');
  const unlock = await txt('.unlock');
  ok(has(unlock, /1\s*of\s*2/), 'unlock card: 1 of 2 must-haves', unlock);
  ok(has(unlock, 'Power-Line Installers'), 'unlock card: Power-Line Installers now ready', unlock);
  ok(has(unlock, /\b10[0-9]\b/) && has(unlock, 'jobs'), 'unlock card: about 106 jobs with every must-have', unlock);
  say(`        unlock card says: ${unlock.slice(0, 220)}`);
  await shot('06-unlock'); await p.click('.unlock .cta');

  if (!SHORT) {
  head(7, 'Explore → Search "conduit installer"; open Electricians; save three jobs');
  await p.click('.tb >> text="Explore"'); await p.click('.tabpane .tabs >> text=Search');
  await p.fill('#occ-search', 'conduit installer'); await p.waitForSelector('.aka');
  ok(has(await txt('.tabpane'), 'also called', 'Conduit Installer'), 'Electricians found by another name ("also called Conduit Installer")');
  await p.click('.tabpane button.occ:has-text("Electricians")'); await p.waitForSelector('.page .sheet-title');
  const jobPage = await txt('.page-body');
  ok(has(jobPage, 'Tools of the trade'), 'job page: tools of the trade', jobPage);
  ok(has(jobPage, 'Software you', 'Jobs like this'), 'job page: software and "Jobs like this"', jobPage);
  await p.click('.page-foot >> text=Save this job'); await p.waitForSelector('.page-foot >> text=Saved'); await p.click('.back');
  for (const q of ['power-line', 'boilermakers']) {
    await p.fill('#occ-search', q); await p.waitForTimeout(600); await p.click('.tabpane button.occ >> nth=0');
    await p.waitForSelector('.page .sheet-title'); await p.click('.page-foot >> text=Save this job'); await p.waitForSelector('.page-foot >> text=Saved'); await p.click('.back');
  }
  ok(true, 'three jobs saved');

  head(8, 'Explore → Interests: twelve questions, jobs that fit');
  await p.click('.tabpane .tabs >> text=Interests'); await p.waitForSelector('.qz');
  const qs = p.locator('.qz'); const n = await qs.count();
  ok(n === 12, 'twelve questions', n);
  for (let i = 0; i < n; i++) {
    const t = await qs.nth(i).locator('p').textContent();
    const a = /Fix a broken|Build or install|Check numbers/.test(t) ? "I'd enjoy it" : /Keep records|Solve a tricky/.test(t) ? 'Maybe' : 'Not for me';
    await qs.nth(i).locator(`.qa:has-text("${a}")`).click();
  }
  await shot('08-quiz'); await p.click('.tabpane .cta'); await p.waitForSelector('.tabpane .fit');
  const quiz = await txt('.tabpane');
  ok(has(quiz, 'You lean towards') && (await p.locator('.tabpane .list .occ').count()) >= 5, 'results: "You lean towards…" and a list of jobs', quiz);
  ok(has(quiz, /simplified/i), 'screen says it is a simplified version', quiz);

  head(9, 'Skills → Repairing → I can already: the goal is complete (2 of 2)');
  await p.click('.tb >> text="Skills"'); await p.waitForSelector('.skillrow');
  await p.click('.skillrow:has-text("Repairing")'); await p.waitForSelector('.skillstate');
  await p.click('.page >> text=I can already'); await p.waitForSelector('.unlock');
  const u2 = await txt('.unlock');
  ok(has(u2, /2\s*of\s*2/), 'unlock card: 2 of 2 must-haves', u2);
  ok(has(u2, /You now have everything this job depends on/), '"You now have everything this job depends on"', u2);
  ok(has(u2, /\b13[0-9]\b/), 'about 131 jobs with every must-have', u2);
  say(`        unlock card says: ${u2.slice(0, 220)}`);
  await shot('09-complete'); await p.click('.unlock .cta'); await p.click('.back');

  head(10, 'Home → Saved jobs → tick three → Compare; Your progress 0 → 0 → 1 → 2');
  await p.click('.tb >> text="Home"'); await p.waitForSelector('.svd');
  await p.click('.pick >> nth=0'); await p.click('.pick >> nth=1'); await p.click('.pick >> nth=2');
  await p.click('text=Compare 3 jobs'); await p.waitForSelector('.cmpcol');
  ok((await p.locator('.cmpcol').count()) === 3, 'compare shows three columns');
  await shot('10-compare'); await p.click('.back');
  const prog = await txt('.card:has-text("Your progress")');
  ok(has(prog, /0\s*→\s*0\s*→\s*1\s*→\s*2/), 'progress: 0 → 0 → 1 → 2', prog);

  }
  head(11, 'Home → Check my CV: skills with quoted lines; Add Repairing; goal check; never saved');
  await p.click('.cvcard .btn'); await p.waitForSelector('#cv-text');
  await p.click('text=Use an example CV'); await p.click('text=Check my CV >> nth=-1'); await p.waitForSelector('.cvs');
  const cvSkills = await p.locator('.cvs .ps-t b').allTextContents();
  ok(cvSkills.some((s) => /Repairing/.test(s)), 'CV suggests Repairing', cvSkills.join(', '));
  const cv = await txt('.page-body');
  ok(has(cv, 'never saved'), 'screen says "never saved"', cv);
  ok(has(cv, 'Multimeters', 'Microsoft Excel'), 'goal check names Multimeters and Microsoft Excel', cv);
  ok(has(cv, /Troubleshooting\s*—\s*not shown yet/), 'Troubleshooting "not shown yet"', cv);
  await shot('11-cv');
  if (SHORT) {   // on the short path Troubleshooting is held (step 6), so adding Repairing completes the goal
    await p.click('.cvs:has-text("Repairing") >> text=Add to my skills'); await p.waitForSelector('.unlock');
    const u3 = await txt('.unlock');
    ok(has(u3, /2\s*of\s*2/), 'adding Repairing from the CV: unlock card 2 of 2 must-haves', u3);
    ok(has(u3, /You now have everything this job depends on/), '"You now have everything this job depends on"', u3);
    await shot('11b-cv-unlock'); await p.click('.unlock .cta');
  }
  await p.click('.back');

  head(12, 'Home → What employers ask for: Electricians, US adverts, April 2024');
  await p.click('text=See what employers ask for'); await p.waitForSelector('.emp');
  const emp = await txt('.emp');
  ok(has(emp, /From 84 real adverts/), '84 real adverts', emp);
  ok(has(emp, 'United States', 'April 2024'), 'labelled United States, April 2024', emp);
  ok(has(emp, /closed/i), 'says they have closed', emp);
  ok(has(emp, /Of the 73 adverts that said/) && has(emp, /7 in 10\s*were open to beginners/), '7 in 10 of the 73 that state a level were open to beginners', emp);
  ok(has(emp, /7 in 10\s*A licence or certificate/), '7 in 10 mention a trade licence', emp);
  ok(has(emp, /3 in 10\s*A driver/), '3 in 10 mention a driver\'s licence', emp);
  const stressed = emp.slice(emp.indexOf('talk about most'));
  ok(has(stressed, 'Installation', 'Repairing', 'Troubleshooting'), 'skills they stress: Installation, Repairing, Troubleshooting', stressed);
  await shot('12-employers'); await p.click('.back');

  head(13, 'Home → Practise for an interview: "I fixed it." 2 of 7; a full story 7 of 7');
  await p.click('text=Start practising'); await p.waitForSelector('.qtext');
  await p.click('.qdot >> nth=1');
  const q2 = await txt('.qtext'); say(`        question 2: ${q2}`);
  ok(has(await txt('.page-body'), 'Troubleshooting'), 'question 2 is about Troubleshooting');
  await p.fill('#answer', 'I fixed it.'); await p.click('text=Get feedback'); await p.waitForSelector('.fbk');
  const weak = await txt('.fbk .big-count');
  ok(/^2 of 7/.test(weak), '"I fixed it." meets 2 of 7', weak);
  await p.fill('#answer', "Last year at my uncle's house the kitchen lights stopped working. I checked the plug points with a multimeter and found a loose wire in the switch. I switched off the power at the board, tightened the wire and tested it again. In the end the lights worked and my uncle saved paying an electrician R450. I learned to always test before and after.");
  await p.click('text=Get feedback'); await p.waitForFunction(() => /^7 of 7/.test(document.querySelector('.fbk .big-count').textContent.trim()));
  ok(true, 'the full story meets 7 of 7'); await shot('13-practice'); await p.click('.back');

  head(14, 'Me → Print my plan; note the code; sign out; sign back in with the code');
  await p.click('.tb >> text="Me"'); await p.waitForSelector('#me-name');
  const code = (await txt('.codecard .code')).replace(/\s/g, '');
  ok(/^[A-Z0-9]{6}$/.test(code.replace(/-/g, '')), 'a six-character plan code is shown', code);
  await p.evaluate(() => { window.print = () => { window.__printed = true; }; });
  await p.click('text=Print my plan'); await p.waitForFunction(() => window.__printed);
  ok(true, 'Print my plan builds a page and calls print');
  await shot('14-me');
  await p.click('text=Sign out on this device'); await p.waitForSelector('.hero');
  await p.click('text=I have a plan code'); await p.fill('#welcome-code', code); await p.click('.door .cta'); await p.waitForSelector('.hello');
  ok(has(await txt('.hello'), 'Thabo'), 'the plan comes back with the plan code', await txt('.hello'));
  const back = await txt('.pane');
  ok(has(back, 'Electricians'), 'the goal (Electricians) is still there after signing back in', back);

  head(15, 'For the marker: ?presenter brings the codes and ratings back');
  await p.goto(BASE + '/?presenter'); await p.waitForSelector('.hello');
  const pres = await txt('body');
  ok(/47-2111/.test(pres) || /Job Zone/.test(pres) || /FR-0/.test(pres), 'presenter mode shows requirement ids / SOC codes / Job Zones', pres.slice(0, 200));

  say('');
  ok(errs.length === 0, 'no console or page errors during the whole walk', errs.join(' | '));
  say(fails ? `\n${fails} CHECK(S) FAILED — see above` : '\nDEMO PATH OK: every number in the script matches the app');
  process.exitCode = fails ? 1 : 0;
  await b.close();
})().catch((e) => { console.error(`\nWALK STOPPED at step ${step}: ${e.message.split('\n')[0]}`); process.exit(2); });
