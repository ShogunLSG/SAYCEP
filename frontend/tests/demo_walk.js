/* The final demo, run by machine: docs/presentation.md §3, step by step.
 *
 * One profile — school-leaver, installation and maintenance skills — aiming at
 * Electricians. It checks the numbers the script says out loud. If one drifts,
 * it fails on that step and says which.
 *
 * Test-time only; needs Playwright and the server on port 8000:
 *   node frontend/tests/demo_walk.js
 *   SHOTS=/some/folder node frontend/tests/demo_walk.js     also saves a screenshot per step
 *   BASE=http://127.0.0.1:8001 node frontend/tests/demo_walk.js   another address or port
 * Exit code 0 only if every check passed and the page logged no errors.
 */
const { chromium } = require('playwright');
const SHOTS = process.env.SHOTS;
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
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
  let expect404 = false;
  p.on('console', (m) => m.type() === 'error' && !/CERT|fonts/.test(m.text()) && !(expect404 && /404/.test(m.text())) && errs.push(m.text()));
  const txt = (sel) => p.textContent(sel).then((t) => (t || '').replace(/\s+/g, ' ').trim());
  const shot = async (n) => { if (SHOTS) { await p.waitForTimeout(500); await p.screenshot({ path: `${SHOTS}/${n}.png` }); } };
  const head = (n, t) => { step = n; say(`\nStep ${n}  ${t}`); };
  const cta = () => p.click('.foot .cta');

  head(1, 'Welcome: a first name, no email or password');
  await p.goto(BASE + '/'); await p.waitForSelector('.hero');
  ok(has(await txt('.hero'), 'Find a career you can actually reach'), 'welcome screen shows the headline');
  ok(has(await txt('.door'), /plan code/i) && has(await txt('.door'), /no email/i), 'the door offers a plan code and says "No email, no password"');
  await p.click('text=I have a plan code');
  ok(await p.locator('.door .cta').isDisabled(), 'sign-in stays disabled until a full six-character code is typed');
  expect404 = true;
  await p.fill('#welcome-code', 'ZZZZZZ'); await p.click('.door .cta'); await p.waitForSelector('.door .banner'); expect404 = false;
  ok(has(await txt('.door .banner'), 'No plan matches that code'), 'a wrong plan code gets a plain message');
  await p.click("text=I'm new");
  await p.fill('#welcome-name', 'Thabo'); await p.click('.door .cta');

  head(2, 'I left school, tick the six installation and maintenance skills');
  await p.click('text=I left school'); await cta();
  for (const k of ['Installation', 'Equipment Maintenance', 'Troubleshooting', 'Active Listening', 'Critical Thinking', 'Coordination'])
    await p.click(`button.chip[aria-label="${k}"]`);
  ok((await p.locator('button.chip[aria-pressed="true"]').count()) === 6, 'six skills ticked');
  await shot('02-skills'); await cta(); await p.waitForSelector('.occ');

  head(3, 'For you: electrical trades, Helpers--Electricians; Search "electric"; Electricians');
  const forYou = await txt('.pane');
  ok(has(forYou, 'Because you have'), 'each recommendation says why');
  ok(has(forYou, 'Millwrights') && has(forYou, 'Helpers--Electricians'), 'For you includes Millwrights and Helpers--Electricians', forYou);
  await shot('03-for-you');
  await p.click('.tabs >> text=Search'); await p.fill('#occ-search', 'electric'); await p.waitForSelector('text=Electricians');
  await p.click('button.occ:has-text("Electricians")'); await p.waitForSelector('.sheet-title');
  ok(has(await txt('.sheet'), 'Electricians', 'A day in this job'), 'job panel shows Electricians and "A day in this job"');
  await shot('03b-electricians'); await p.click('.sheet-foot .cta'); await cta();

  head(4, 'The gap: 6 of 34 held, 2 must-haves, 1 missing (Repairing)');
  await p.waitForSelector('.headline');
  const gap = await txt('.pane');
  ok(has(gap, /6 of the 34/), '"6 of the 34" skills already held', gap);
  ok(has(gap, /1 must-have/i), 'one must-have still to learn', gap);
  ok(has(gap, 'Repairing'), 'the missing must-have is Repairing', gap);
  await shot('04-gap'); await cta(); await p.waitForSelector('.steps');

  head(5, 'The route: a helper role one level down, then Electricians (ADR-0034)');
  const route = await txt('.steps');
  const order = ['Helpers--Electricians', 'Electricians'].map((t, k) => route.indexOf(t, k === 0 ? 0 : route.indexOf('Helpers--Electricians') + 10));
  ok(order.every((i) => i >= 0) && order[1] > order[0],
     'route order: Helpers--Electricians → Electricians', route);
  ok(!has(route, 'Powerhouse') || has(route, 'Also at this level'), 'repair roles are not steps (at most listed as alternatives)');
  ok(has(route, /Start here/), 'the first step says "Start here"');
  ok(has(route, /Leads to the next step/), 'the step says why it leads to the next');
  ok(has(route, 'Also at this level'), 'same-level jobs are listed as alternatives');
  await shot('05-route'); await cta(); await p.waitForSelector('.hello');

  head(6, 'Home: Repairing → Start learning; the card must not move');
  ok(has(await txt('.hello'), 'Thabo'), 'Home greets by name');
  ok(has(await txt('.readiness, .ready'), /1\s*of\s*2/), 'goal card starts at 1 of 2 must-haves');
  await p.click('.ps:has-text("Repairing") >> text=Start learning'); await p.waitForSelector('.ps.learning');
  ok(has(await txt('.readiness, .ready'), /1\s*of\s*2/), 'learning changes nothing: still 1 of 2');
  await shot('06-learning');

  head(7, 'CV: example CV suggests Repairing; adding it closes the goal');
  await p.click('.cvcard .btn'); await p.waitForSelector('#cv-text');
  await p.fill('#cv-text', 'hi');
  ok(await p.locator('button:has-text("Check my CV")').last().isDisabled(), 'the CV check refuses text that is too short');
  await p.fill('#cv-text', '');
  await p.click('text=Use an example CV'); await p.click('text=Check my CV >> nth=-1'); await p.waitForSelector('.cvs');
  const cvSkills = await p.locator('.cvs .ps-t b').allTextContents();
  ok(cvSkills.some((s) => /Repairing/.test(s)), 'CV suggests Repairing', cvSkills.join(', '));
  const cv = await txt('.page-body');
  ok(has(cv, 'never saved'), 'screen says "never saved"');
  await shot('07-cv');
  await p.click('.cvs:has-text("Repairing") >> text=Add to my skills'); await p.waitForSelector('.unlock');
  const u = await txt('.unlock');
  ok(has(u, /2\s*of\s*2/) || has(u, /everything this job depends on/), 'adding Repairing completes the goal (2 of 2)', u);
  await shot('07b-cv-unlock'); await p.click('.unlock .cta'); await p.click('.tb >> text="Home"');

  head(8, 'Home → What employers ask for: Electricians, US adverts, April 2024');
  await p.click('text=See what employers ask for'); await p.waitForSelector('.emp');
  const emp = await txt('.emp');
  ok(has(emp, /From 84 real adverts/), '84 real adverts', emp);
  ok(has(emp, 'United States', 'April 2024'), 'labelled United States, April 2024');
  ok(has(emp, /closed/i), 'says they have closed');
  ok(has(emp, /Of the 73 adverts that said/) && has(emp, /7 in 10\s*were open to beginners/), '7 in 10 of the 73 were open to beginners');
  await shot('08-employers'); await p.click('.back');

  head(9, 'Interview: "I fixed it." 2 of 7; a full story 7 of 7');
  await p.click('text=Start practising'); await p.waitForSelector('.qtext');
  await p.click('.qdot >> nth=1');
  ok(has(await txt('.page-body'), 'Troubleshooting'), 'question 2 is about Troubleshooting');
  await p.fill('#answer', 'I fixed it.'); await p.click('text=Get feedback'); await p.waitForSelector('.fbk');
  ok(/^2 of 7/.test(await txt('.fbk .big-count')), '"I fixed it." meets 2 of 7', await txt('.fbk .big-count'));
  await p.fill('#answer', "Last year at my uncle's house the kitchen lights stopped working. I checked the plug points with a multimeter and found a loose wire in the switch. I switched off the power at the board, tightened the wire and tested it again. In the end the lights worked and my uncle saved paying an electrician R450. I learned to always test before and after.");
  await p.click('text=Get feedback'); await p.waitForFunction(() => /^7 of 7/.test(document.querySelector('.fbk .big-count').textContent.trim()));
  ok(true, 'the full story meets 7 of 7'); await shot('09-practice'); await p.click('.back');

  head(10, 'Me → Print my plan; note the code; sign out; sign back in');
  await p.click('.tb >> text="Me"'); await p.waitForSelector('#me-name');
  const code = (await txt('.codecard .code')).replace(/\s/g, '');
  ok(/^[A-Z0-9]{6}$/.test(code.replace(/-/g, '')), 'a six-character plan code is shown', code);
  await p.evaluate(() => { window.print = () => { window.__printed = true; }; });
  await p.click('text=Print my plan'); await p.waitForFunction(() => window.__printed);
  ok(true, 'Print my plan builds a page and calls print');
  await p.click('text=Sign out on this device'); await p.waitForSelector('.hero');
  await p.click('text=I have a plan code'); await p.fill('#welcome-code', code); await p.click('.door .cta'); await p.waitForSelector('.hello');
  ok(has(await txt('.hello'), 'Thabo'), 'the plan comes back with the plan code');
  ok(has(await txt('.pane'), 'Electricians'), 'the goal is still Electricians after signing back in');

  head(11, 'For the marker: ?presenter brings the codes and ratings back');
  await p.goto(BASE + '/?presenter'); await p.waitForSelector('.hello');
  ok(/47-2111/.test(await txt('body')) || /Job Zone/.test(await txt('body')) || /FR-0/.test(await txt('body')), 'presenter mode shows requirement ids / SOC codes / Job Zones');

  say('');
  ok(errs.length === 0, 'no console or page errors during the whole walk', errs.join(' | '));
  say(fails ? `\n${fails} CHECK(S) FAILED — see above` : '\nDEMO PATH OK: every number in the script matches the app');
  process.exitCode = fails ? 1 : 0;
  await b.close();
})().catch((e) => { console.error(`\nWALK STOPPED at step ${step}: ${e.message.split('\n')[0]}`); process.exit(2); });
