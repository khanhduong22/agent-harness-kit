// Puppeteer is NOT a dependency of this skill and never will be: the render-side
// gates are optional, and a skill that can be read as text should not drag a
// browser download behind it. So this module RESOLVES an install that already
// exists on the machine, and never assumes one.
//
// `puppeteer-core` FIRST (user ruling 2026-09-02: "xài puppeteer-core, không tải
// thêm browser lần hai"). The full `puppeteer` package downloads its own Chrome on
// install -- a second 340 MB browser next to the chrome-headless-shell the render
// profile pins -- and the pipeline never launches that Chrome. `puppeteer-core` is
// the same client without the download; the browser it drives is the ONE the
// profile names, through PUPPETEER_EXECUTABLE_PATH (data/render-profiles/*.json,
// `headless.env`). A repo-root `npm install` gives exactly that (package.json pins
// the client to the version that speaks chrome-headless-shell 148's protocol).
//
// Resolution order, no machine-local default (there used to be an absolute
// /Users/... path here, which made the checks work on exactly one laptop and
// fail everywhere else with a message naming a stranger's home directory):
//   1. PUPPETEER_RESOLVE_DIR -- any directory from which `require("puppeteer-core")`
//      or `require("puppeteer")` resolves, in that order. The TRAILING SLASH
//      matters: createRequire treats a bare path as a FILE and resolves relative
//      to its parent.
//   2. a plain `import("puppeteer-core")`, then `import("puppeteer")` -- the
//      repo root's installed packages, an npm link, or a global install via NODE_PATH.
//
// If none works the process exits 2 with the UNVERIFIED banner below. That
// exit code is the contract the calling scripts and the pre-delivery checklist
// rely on: 0 pass, 1 violation (or empty element set), 2 could-not-run. A cut
// delivered after a code-2 skip is an UNVERIFIED cut and must SAY SO in
// delivery -- silence would read as a pass.
import { createRequire } from "node:module";

export const RESOLVE_DIR = process.env.PUPPETEER_RESOLVE_DIR || null;

export const UNVERIFIED_BANNER = [
  "UNVERIFIED -- puppeteer not available; render-side checks did not run.",
  "       Run the browser checks on a machine that has puppeteer, or point",
  "       PUPPETEER_RESOLVE_DIR at a directory (TRAILING SLASH) from which",
  '       require("puppeteer") resolves -- e.g. the chrome-devtools skill\'s',
  "       scripts/ directory, or any node project that installed it.",
  "       Anything delivered without these checks must be labelled UNVERIFIED",
  "       in the response; never report it as passing.",
].join("\n");

// puppeteer-core ships no browser, so it must be TOLD which one. The render profile
// pins that path; without it the client would guess at a cache this machine may not
// have, and a guess is not a pinned envelope.
export const NO_BINARY_BANNER = [
  "UNVERIFIED -- puppeteer-core resolved but PUPPETEER_EXECUTABLE_PATH is unset.",
  "       Export the binary the render profile pins (data/render-profiles/",
  "       swiftshader-1.json -> headless.env) before running a browser check.",
].join("\n");

const CLIENTS = ["puppeteer-core", "puppeteer"];

let puppeteer = null;
let resolveError = null;
export let resolvedPackage = null;

if (RESOLVE_DIR) {
  const req = createRequire(RESOLVE_DIR);
  for (const name of CLIENTS) {
    try { puppeteer = req(name); resolvedPackage = name; break; }
    catch (err) { resolveError = new Error(`PUPPETEER_RESOLVE_DIR=${RESOLVE_DIR}: ${err.message}`); }
  }
}

if (!puppeteer) {
  for (const name of CLIENTS) {
    try { puppeteer = (await import(name)).default; resolvedPackage = name; resolveError = null; break; }
    catch (err) { resolveError = resolveError || err; }
  }
}

if (!puppeteer) {
  console.error(`${UNVERIFIED_BANNER}\n       (${resolveError && resolveError.message})`);
  process.exit(2);
}
if (resolvedPackage === "puppeteer-core" && !process.env.PUPPETEER_EXECUTABLE_PATH) {
  console.error(NO_BINARY_BANNER);
  process.exit(2);
}

// `puppeteer-core` does not read PUPPETEER_EXECUTABLE_PATH on its own -- only the full package's
// configuration loader does -- so the pinned binary is injected into every `launch()` here, once,
// instead of at each of the callers. A caller that names its own `executablePath` wins. Every other
// member is passed through bound to the real instance.
const EXECUTABLE = process.env.PUPPETEER_EXECUTABLE_PATH || null;
const launched = new Proxy(puppeteer, {
  get(target, key) {
    if (key === "launch") {
      return (options = {}) => target.launch(EXECUTABLE && !options.executablePath
        ? { executablePath: EXECUTABLE, ...options } : options);
    }
    const value = target[key];
    return typeof value === "function" ? value.bind(target) : value;
  },
});

export default launched;
