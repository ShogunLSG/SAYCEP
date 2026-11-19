/* SAYCEP — reading an uploaded CV in the browser (ADR-0023, docs/plans/cv-upload.md).
 *
 * The file never leaves the device: its text is pulled out here and put in
 * the CV box, where the user can check it before scanning. Only that text is
 * sent, exactly as when it's pasted, so the scanner and its measured r = 0.27
 * (ADR-0014) are unchanged.
 *
 *   .txt   read directly
 *   .docx  a zip of XML: word/document.xml, unzipped with the browser's own
 *          DecompressionStream -- no library
 *   .pdf   pdf.js (Mozilla, Apache-2.0), vendored and loaded only when needed
 */

const CV_MAX_BYTES = 5 * 1024 * 1024;
const CV_MAX_CHARS = 15000;               // the scanner's own limit
const PDFJS = "/static/vendor/pdf-3.11.174.min.js";

class CvFileError extends Error {}

async function readCvFile(file) {
  const name = (file.name || "").toLowerCase();
  if (file.size > CV_MAX_BYTES) throw new CvFileError("That file is over 5 MB. Try a smaller copy, or paste the text instead.");
  let text;
  if (name.endsWith(".txt")) text = await file.text();
  else if (name.endsWith(".docx")) text = await docxText(await file.arrayBuffer());
  else if (name.endsWith(".pdf")) text = await pdfText(await file.arrayBuffer());
  else throw new CvFileError("Upload a PDF, a Word file (.docx) or a text file. Older .doc files: save as .docx first.");
  text = tidy(text);
  if (text.length < 20) {
    throw new CvFileError(name.endsWith(".pdf")
      ? "This looks like a scanned document, so there's no text to read. Paste the text instead."
      : "We couldn't find any text in that file. Paste the text instead.");
  }
  const cut = text.length > CV_MAX_CHARS;
  return { text: cut ? text.slice(0, CV_MAX_CHARS) : text, cut };
}

/** Bullets and symbol-font characters as plain text. Word's bullets come out
 *  of PDFs as private-use characters (U+F0B7 and friends) that show as boxes. */
function tidy(text) {
  return text
    .replace(/^([ \t]*)[\uE000-\uF8FF\u2022\u25AA\u25CF\u25E6\u2023\u2043]+[ \t]*/gm, "$1- ")
    .replace(/[\uE000-\uF8FF]/g, "")
    .replace(/\u00A0/g, " ")
    .replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** The text of a .docx: one line per paragraph, tabs as spaces. */
async function docxText(buf) {
  const xml = await zipEntry(buf, "word/document.xml");
  if (!xml) throw new CvFileError("That doesn't look like a Word document. Paste the text instead.");
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
  return [...doc.getElementsByTagNameNS(W, "p")].map((p) => {
    let line = "";
    for (const n of p.getElementsByTagNameNS(W, "*")) {
      if (n.localName === "t") line += n.textContent;
      else if (n.localName === "tab") line += " ";
      else if (n.localName === "br") line += "\n";
    }
    return line;
  }).join("\n");
}

/** One file out of a zip, as text, by reading the central directory. */
async function zipEntry(buf, wanted) {
  const v = new DataView(buf);
  let eocd = -1;
  for (let i = buf.byteLength - 22; i >= Math.max(0, buf.byteLength - 65557); i--) {
    if (v.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) return null;
  let p = v.getUint32(eocd + 16, true);
  const count = v.getUint16(eocd + 10, true);
  const dec = new TextDecoder();
  for (let k = 0; k < count && v.getUint32(p, true) === 0x02014b50; k++) {
    const method = v.getUint16(p + 10, true), size = v.getUint32(p + 20, true);
    const nameLen = v.getUint16(p + 28, true), extra = v.getUint16(p + 30, true), comment = v.getUint16(p + 32, true);
    const local = v.getUint32(p + 42, true);
    const name = dec.decode(new Uint8Array(buf, p + 46, nameLen));
    if (name === wanted) {
      const start = local + 30 + v.getUint16(local + 26, true) + v.getUint16(local + 28, true);
      const raw = new Uint8Array(buf, start, size);
      if (method === 0) return dec.decode(raw);
      if (method !== 8) return null;
      const out = new Blob([raw]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
      return new Response(out).text();
    }
    p += 46 + nameLen + extra + comment;
  }
  return null;
}

let pdfjsReady = null;
function loadPdfJs() {
  pdfjsReady = pdfjsReady || new Promise((ok, fail) => {
    const s = document.createElement("script");
    s.src = PDFJS;
    s.onload = () => { window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS.replace(".min.js", ".worker.min.js"); ok(window.pdfjsLib); };
    s.onerror = () => { pdfjsReady = null; fail(new CvFileError("The PDF reader didn't load. Paste the text instead.")); };
    document.head.appendChild(s);
  });
  return pdfjsReady;
}

/** The text of a PDF, page by page. isEvalSupported is off: the fix for
 *  CVE-2024-4367 in this pdf.js version. */
async function pdfText(buf) {
  const lib = await loadPdfJs();
  let pdf;
  try { pdf = await lib.getDocument({ data: new Uint8Array(buf), isEvalSupported: false }).promise; }
  catch (_) { throw new CvFileError("That PDF couldn't be opened. Paste the text instead."); }
  const pages = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const tc = await (await pdf.getPage(i)).getTextContent();
    pages.push(tc.items.map((it) => it.str + (it.hasEOL ? "\n" : "")).join(""));
  }
  return pages.join("\n");
}
