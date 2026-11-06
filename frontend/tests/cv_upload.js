/* CV upload in the browser (ADR-0023): a real browser, real files.
 *
 * Uploads the fixtures in frontend/tests/fixtures/ to the CV check:
 *   - plain and designed CVs as Word, PDF (from Word and from Chrome, one and
 *     two pages, two columns, bullets) and text;
 *   - the edge cases: upper-case extension, uncompressed .docx, accented and
 *     isiZulu text, a CV over the 15,000-character limit, the same file twice;
 *   - the refusals: a scanned (text-less) PDF, a corrupt PDF, a corrupt .docx,
 *     an old .doc, a picture, a file over 5 MB;
 * and checks the text, the messages, that a scan of uploaded text works, and
 * that no file is ever sent to the server -- only the text, as when pasted.
 *
 * Test-time only; needs Playwright (NODE_PATH) and the server on port 8000:
 *   node frontend/tests/cv_upload.js
 *   BASE=http://127.0.0.1:8001 node frontend/tests/cv_upload.js
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const BASE = process.env.BASE || 'http://127.0.0.1:8000';
const FIX = path.join(__dirname, 'fixtures');
let failed = 0, passed = 0;
const check = (name, ok, detail = '') => {
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  -- ' + detail : ''}`);
  ok ? passed++ : failed++;
};

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
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('request', (r) => { if (r.method() !== 'GET') bodies.push([r.url(), r.headers()['content-type'] || '', r.postData() || '']); });
  await p.goto(BASE);
  await p.evaluate((id) => localStorage.setItem('saycep.plan', id), prof.profile_id);
  await p.goto(BASE);
  await p.click('.cvcard .btn');
  await p.waitForSelector('#cv-file');

  const box = () => p.inputValue('#cv-text');
  const msg = () => p.textContent('.cvup-msg');
  const upload = async (file) => {
    await p.setInputFiles('#cv-file', typeof file === 'string' ? path.join(FIX, file) : file);
    await p.waitForFunction(() => !/^Reading /.test(document.querySelector('.cvup-msg').textContent), null, { timeout: 20000 });
  };
  const scan = async () => {
    await p.click('.page button:has-text("Check my CV")');
    await p.waitForSelector('#cv-found');
    return p.$$eval('.cvs .ps-t b', (xs) => xs.map((x) => x.textContent));
  };
  const boxes = (t) => /[-�]/.test(t);   // symbol-font leftovers or broken characters

  console.log('\nCV upload: the files a CV comes as  (ADR-0023)');
  await upload('cv-example.docx');
  let t = await box();
  check('a Word file fills the box, one line per paragraph',
    t.startsWith('Thabo Mokoena') && t.includes('multimeter') && t.split('\n').length >= 8, `${t.length} chars`);
  check('the message names the file and says to check the text', (await msg()).includes('Read cv-example.docx'));
  await upload('cv-example.pdf');
  t = await box();
  check('a PDF fills the box', t.includes('Thabo Mokoena') && t.includes('hardware store'), `${t.length} chars`);
  check('the uploaded text scans like pasted text: skills found', (await scan()).length > 0);
  await upload('cv-example.txt');
  check('a text file is read directly', (await box()).includes('circuit diagrams'));

  console.log('\nCV upload: designed CVs (two columns, a table, bullets, headings)');
  for (const [f, what] of [['cv-designed.docx', 'Word'], ['cv-designed.pdf', 'PDF exported from Word'],
                           ['cv-two-pages.pdf', 'two-page PDF printed from a browser']]) {
    await upload(f);
    t = await box();
    check(`${what}: both columns and every section are read`,
      ['Lerato Nkosi', 'Using a multimeter', 'Pick n Pay', 'Repaired broken lights', 'National Senior Certificate']
        .every((s) => t.includes(s)), `${t.length} chars`);
    check(`${what}: the last page is read too`, t.includes('Employee of the month'));
    check(`${what}: bullets come out as plain dashes, with no boxes`, !boxes(t) && !t.includes('•'),
      JSON.stringify(t.split('\n').find((l) => /Served customers/.test(l))));
    const found = await scan();
    check(`${what}: the scan finds Repairing and Equipment Maintenance`,
      found.includes('Repairing') && found.includes('Equipment Maintenance'), found.join(', '));
  }

  console.log('\nCV upload: edge cases');
  await upload('CV-UPPER.PDF');
  check('an upper-case extension (.PDF) is accepted', (await box()).includes('Thabo Mokoena'));
  await upload('cv-stored.docx');
  check('a .docx saved without compression is read', (await box()).includes('Pick n Pay'));
  await upload('cv-unicode.txt');
  t = await box();
  check('accents, dashes and isiZulu survive', t.includes('Émalahleni') && t.includes('Sipho Ndlovu – Umsebenzi') && t.includes('Ngisebenze'));
  await upload('cv-long.txt');
  t = await box();
  check('a CV over 15,000 characters is cut to the limit, and the message says so',
    t.length === 15000 && /only the first 15,000 characters/.test(await msg()), `${t.length} chars`);
  await upload('cv-example.docx');
  await upload('cv-example.docx');
  check('the same file can be chosen twice in a row', (await msg()).includes('Read cv-example.docx'));
  check('the file control is a labelled input', (await p.getAttribute('label[for="cv-file"]', 'for')) === 'cv-file');

  console.log('\nCV upload: refusals, each with a plain message and the box left alone');
  const refusals = [
    ['cv-scanned.pdf', /scanned document/, 'a scanned PDF (no text layer)'],
    ['cv-corrupt.pdf', /couldn't be opened/, 'a corrupt PDF'],
    ['cv-corrupt.docx', /doesn't look like a Word document/, 'a corrupt .docx'],
    ['cv-old.doc', /save as \.docx/, 'an old .doc file'],
    ['not-a-cv.png', /Upload a PDF, a Word file/, 'a picture'],
    [{ name: 'huge.pdf', mimeType: 'application/pdf', buffer: Buffer.alloc(5 * 1024 * 1024 + 1, 0x25) }, /over 5 MB/, 'a file over 5 MB'],
  ];
  for (const [f, rx, what] of refusals) {
    await p.fill('#cv-text', 'unchanged');
    await upload(f);
    check(`${what}: refused`, rx.test(await msg()) && (await box()) === 'unchanged'
      && (await p.getAttribute('.cvup-msg', 'class')).includes('bad'), await msg());
  }
  await upload('cv-example.pdf');
  check('after a refusal, a good file works again and the message is no longer an error',
    (await box()).includes('Thabo') && !(await p.getAttribute('.cvup-msg', 'class')).includes('bad'));

  console.log('\nCV upload: privacy');
  const scans = bodies.filter(([u]) => u.endsWith('/cv/scan'));
  check('only text is sent: every request is JSON, never a file', bodies.every(([, ct]) => ct.includes('application/json'))
    && scans.length === 4, `${scans.length} scans; ${[...new Set(bodies.map(([u, ct]) => u.replace(BASE, '') + ' ' + ct))].join('; ')}`);
  check('no request carries PDF or Word file bytes',
    bodies.every(([, , d]) => !d.includes('%PDF') && !d.includes('PK\u0003\u0004') && !d.includes('word/document.xml')));
  check('no page or console errors', errs.length === 0, errs.join(' | '));

  await b.close();
  console.log(failed ? `\n${passed} passed, ${failed} FAILED` : `\n${passed} passed. CV UPLOAD OK`);
  process.exitCode = failed ? 1 : 0;
})();
