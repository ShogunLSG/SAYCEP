# Plan: CV file upload

*Written 24 October 2026. Status: **plan only, waiting for go.***

## What changes for the user

On the CV check screen, beside the text box: **"Upload your CV (PDF, Word or
text)"**. The text is pulled out **in the browser** and put into the existing
box, so the user sees exactly what will be scanned and can fix it. Then
"Check my CV" works as now.

## How

- **.txt**: read directly.
- **.docx**: a .docx is a zip of XML. Read `word/document.xml` with the
  browser's built-in `DecompressionStream`, and take the text of each
  paragraph. About 60 lines, no library.
- **.pdf**: **pdf.js** (Mozilla), vendored into `frontend/vendor/` like React,
  so it still works offline. Text from every page, in reading order.
- **Refused, with a plain message:**
  - other file types;
  - files over 5 MB;
  - a PDF with no text layer: "This looks like a scanned document. Paste the
    text instead."
  - text over the existing 15,000-character limit: it is cut, and the screen
    says so.

## What does not change

- **The backend.** There are no new Python packages, and the scoring code is
  unchanged, so the measured r = 0.27 still stands (ADR-0014).
- **Privacy.** The file never leaves the device. Only the text is sent, as now,
  and it is never stored.

## Load-bearing

- **New front-end dependency: pdf.js**, about 1 MB plus its worker, pinned
  to an exact version. Reading PDFs well without it isn't realistic: they use
  compressed streams and font encodings.
- The written requirement for the CV check is yours to draft (FR-11 onward).
  This changes what it can promise: "pasted text or an uploaded PDF, Word or
  text file".

## Tests

- **Unit (Node):** the .docx reader on a small fixture; a scanned-PDF fixture
  gives the scanned message.
- **Demo walk:** upload a fixture PDF CV, check the text box fills, then scan
  it.
- **Accessibility:** the axe audit and the keyboard walk include the upload
  control. It is a real `<input type="file">` with a label.

## Docs

ADR-0022, a row in the report's Q1.2 table ("Partially implemented" becomes
"Implemented: upload or paste; scanned PDFs need pasting"), the slide
features table, `presentation.md` demo path, `STATUS.md`.

## Size

About 2–3 hours.
