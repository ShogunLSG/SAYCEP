/* CV upload in the browser (ADR-0023): a real browser, real files.
 *
 * Uploads the fixtures in frontend/tests/fixtures/ to the CV check and checks
 * that the text lands in the box, that a scan of it works, that a scanned
 * (text-less) PDF and a wrong file type get plain messages, and that no file
 * is ever sent to the server -- only the text, as when it's pasted.
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/cv_upload.js
 *   BASE=http://127.0.0.1:8001 node frontend/tests/cv_upload.js
 */
const { chromium } = require('playwright');
const path = require('path');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
const FIX = path.join(__dirname, 'fixtures');
let failed = 0;
const check = (name, ok, detail = '') => { console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  -- ' + detail : ''}`); if (!ok) failed++; };

(async () => {
  const j = async (p, o) => (await fetch(BASE + p, o)).json();
  const sk = Object.fromEntries((await j('/skills')).skills.map((s) => [s.name, s.element_id]));
  const prof = await j('/profiles', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile_type: 'school_leaver', skills: [sk['Monitoring'], sk['Active Listening']] }) });
  await fetch(`${BASE}/profiles/${prof.profile_id}/target`, { method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ soc_code: '47-2111.00' }) });

  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 460, height: 900 } });
  const errs = [], bodies = [];
  p.on('pageerror', (e) => errs.push(e.message));
  p.on('request', (r) => { if (r.method() !== 'GET') bodies.push([r.url(), r.headers()['content-type'] || '', (r.postData() || '').length]); });
  await p.goto(BASE);
  await p.evaluate((id) => localStorage.setItem('saycep.plan', id), prof.profile_id);
  await p.goto(BASE);
  await p.click('.cvcard .btn');
  await p.waitForSelector('#cv-file');

  const box = () => p.inputValue('#cv-text');
  const msg = () => p.textContent('.cvup-msg');
  const upload = async (file) => {
    await p.setInputFiles('#cv-file', path.join(FIX, file));
    await p.waitForFunction(() => !/^Reading /.test(document.querySelector('.cvup-msg').textContent), null, { timeout: 15000 });
  };

  console.log('\nCV upload  (ADR-0023)');
  await upload('cv-example.docx');
  let t = await box();
  check('a Word file fills the box with its text, one line per paragraph',
    t.startsWith('Thabo Mokoena') && t.includes('multimeter') && t.split('\n').length >= 8, `${t.length} chars`);
  check('the message names the file and says to check it', (await msg()).includes('Read cv-example.docx'));

  await p.fill('#cv-text', '');
  await upload('cv-example.pdf');
  t = await box();
  check('a PDF fills the box with its text', t.includes('Thabo Mokoena') && t.includes('multimeter') && t.includes('hardware store'), `${t.length} chars`);

  await p.click('.page button:has-text("Check my CV")');
  await p.waitForSelector('.cvs');
  check('the uploaded text scans like pasted text: skills found', (await p.locator('.cvs').count()) > 0);

  await upload('cv-example.txt');
  check('a text file is read directly', (await box()).includes('circuit diagrams'));

  await p.fill('#cv-text', 'unchanged');
  await upload('cv-scanned.pdf');
  check('a scanned PDF (no text layer) says so, and leaves the box alone',
    /scanned document/.test(await msg()) && (await box()) === 'unchanged', await msg());

  await upload('not-a-cv.png');
  check('another file type gets a plain message', /Upload a PDF, a Word file/.test(await msg()), await msg());

  const scans = bodies.filter(([u]) => u.endsWith('/cv/scan'));
  check('only text is sent: every request is JSON, never a file upload',
    bodies.every(([, ct]) => ct.includes('application/json')) && scans.length === 1, JSON.stringify(bodies.map(([u, ct]) => [u.replace(BASE, ''), ct])));
  check('no page errors', errs.length === 0, errs.join(' | '));

  await b.close();
  console.log(failed ? `\n${failed} FAILED` : '\nCV UPLOAD OK');
  process.exitCode = failed ? 1 : 0;
})();
