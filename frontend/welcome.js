/* SAYCEP — the front door (ADR-0008).
 *
 * "Signing in" is a plan code, not a password: the only personal detail
 * SAYCEP holds is an optional first name, so there is nothing a password
 * would protect that the code does not. The screen says so plainly.
 */

function Welcome({ onStart, onResume }) {
  const [mode, setMode] = useState("start");       // start | code
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function resume(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    try { await onResume(code); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return html`
    <div class="app welcome">
      <div class="hero">
        <span class="brand big">SAYCEP</span>
        <h1>Find a career you can actually reach.</h1>
        <p>See the skills a job needs, what you already have, and a route to get there —
          including jobs that don't need a degree.</p>
      </div>

      <div class="door">
        <div class="tabs" role="group" aria-label="How to start">
          <button aria-pressed=${mode === "start"} class=${"tab" + (mode === "start" ? " on" : "")}
                  onClick=${() => { setMode("start"); setError(null); }}>I'm new</button>
          <button aria-pressed=${mode === "code"} class=${"tab" + (mode === "code" ? " on" : "")}
                  onClick=${() => { setMode("code"); setError(null); }}>I have a plan code</button>
        </div>

        ${mode === "start"
          ? html`
            <form onSubmit=${(e) => { e.preventDefault(); onStart(name.trim()); }}>
              <label class="field">
                <span>What should we call you? <i>(optional)</i></span>
                <input id="welcome-name" value=${name} maxLength="40" autocomplete="given-name"
                       placeholder="Your first name" onInput=${(e) => setName(e.target.value)} />
              </label>
              <button class="cta" type="submit">Start my plan ${Icon.arrow}</button>
              <p class="fine">No email, no password. We'll give you a plan code at the end
                so you can come back to it on any device.</p>
            </form>`
          : html`
            <form onSubmit=${resume}>
              <label class="field">
                <span>Your plan code</span>
                <input id="welcome-code" class="mono codein" value=${code} maxLength="9"
                       autocomplete="off" autocapitalize="characters" spellcheck="false"
                       placeholder="K7M-2QX" onInput=${(e) => setCode(e.target.value.toUpperCase())} />
              </label>
              ${error && html`<div class="banner">${error}</div>`}
              <button class="cta" type="submit" disabled=${busy || code.replace(/[^A-Z0-9]/gi, "").length < 6}>
                ${busy ? "Opening…" : "Open my plan"}</button>
              <p class="fine">You'll find the code on your plan's home screen.</p>
            </form>`}
      </div>
      <p class="prov">Built on O*NET 29.0 · U.S. Department of Labor · CC BY 4.0</p>
    </div>`;
}
