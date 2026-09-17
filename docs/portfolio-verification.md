# Portfolio verification — 2026-09-16

Baseline: [`b8bf661`](https://github.com/rasasoe/VSH/commit/b8bf66174fa7798bc2dee2f6bdb5dfd3283401bd). This patch fixes API/UI evidence presentation, preserves merged detector rule IDs and repairs test isolation. It does not measure detection accuracy or certify production readiness.

## Results and scope

| Check | Result | Scope |
| --- | --- | --- |
| Full unit suite | **81 passed, no skips** | Runtime, API response, L1/L2, reporting, MCP and in-process dashboard contracts |
| Reverse file order | **81 passed** | Verifies the shared advisory mutation no longer leaks across test files |
| React production build | Passed | `npm ci --ignore-scripts`, `npm run build`; Electron packaging not tested |
| Actual UI + API scan | HTTP 200, 5 findings | Repository fixture; 1 Critical + 4 High; no page errors |
| L2 | mock provider | Demonstrates mapping and UI, not paid-model reasoning quality |
| L3 | Disabled | No SonarQube, Docker PoC or live exploit verification |

Commands from `VSH_Project_MVP`:

```bash
python -m pytest tests/unit -q
cd vsh_desktop
npm ci --ignore-scripts
npm run build
```

The baseline run had 53 passed, 15 failed and 1 skipped. The final suite retains the behaviors under test, adds 12 response cases, and replaces the externally running dashboard requirement with an in-process TestClient. No failing case was marked skip/xfail. Dependency deprecation warnings from TestClient remain.

## What the screenshot proves

[`assets/vsh-local-demo.png`](assets/vsh-local-demo.png) captures the repository React application talking to the real FastAPI scan endpoint with `tests/fixtures/vuln_project`. The capture harness uses an isolated runtime directory, mock L2, disabled L3, and a localhost-only CORS origin for browser rendering. Korean fonts were supplied to the browser. No finding values were injected or edited in the image.

To reproduce interactively, start the backend and desktop using the README, select the fixture, choose mock L2 and disable L3 in Settings, then Scan Project. The browser-rendered capture does not verify Electron's native file picker or Windows installation.

## Corrections and their regression checks

| Problem found | Correction | Protection |
| --- | --- | --- |
| Risk priority shown as severity | Count the actual finding severity | API response tests and real scan comparison |
| L2 text read from absent fields | Join reasoning by vulnerability ID; expose provider/verdict | API response contract |
| `NaN%` confidence | Validate numeric range; show qualitative basis separately | Invalid/valid confidence cases |
| Missing L3 shown as a negative result | Preserve unknown and keep unsupplied L3 evidence empty | API response contract + UI capture |
| Duplicate detector evidence discarded | Retain every contributing rule ID while merging one location | Dedup evidence assertion |
| Shared advisory dictionary modified by tests | Restore each override with monkeypatch | Full suite in normal/reverse order |
| Tests depended on the developer's knowledge/log files | Use temporary repositories with explicit seed fixtures | Per-test isolation |
| Old paths/report API and cached MCP state | Use real fixture paths, current runtime/report contract and fresh MCP module | E2E, report and MCP tests |
| String safety test matched itself and legitimate template names | Test that static scanning neither executes nor changes source | Marker file and source integrity assertions |

## Remaining limits

- Mock/offline advisory data is not a live CVE feed; findings require human review.
- Unit tests and a local fixture scan do not establish precision, recall, real exploitability or load capacity.
- Native Electron packaging, Windows setup, live LLM providers and SonarQube/PoC integration were not revalidated.
- First-run runtime knowledge seeding and production dependency maintenance remain separate operational work.
- The three projects export a shared Finding shape; a unified dashboard is still planned.

GitHub Actions runs the full unit suite, desktop build and README link/image checks. Check the run for the exact commit before relying on a past result.
