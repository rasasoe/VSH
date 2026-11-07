<picture>
  <source media="(max-width: 600px)" srcset="docs/assets/portfolio-banner-mobile.svg">
  <img src="docs/assets/portfolio-banner.svg" width="100%" alt="VSH — Vibe Coding Secure Helper">
</picture>

<p align="right"><a href="README.md">한국어</a> / <strong>English</strong></p>

# VSH — Vibe Coding Secure Helper

**MCP-enabled application security assistant · L1 Detection · L2 LLM Explanation · L3 PoC Validation**  
**Team submission:** February 2026 · **Individual fork improvements:** September 2026

## The idea

As AI-assisted vibe coding accelerates development, insecure code can be introduced just as quickly. VSH asks whether security findings could be surfaced **while a developer edits or saves code**, then explained and accompanied by suggested fixes without breaking the development workflow.

The [team's final MVP-final branch](https://github.com/vmfmgl0607/VSH/tree/MVP-final) contains FastMCP tools and a file-change watcher demo. This personal fork extends Semgrep/tool configuration, Windows wrappers, versioned Finding JSON exports, the React/Electron presentation and tests. Team deliverables are not claimed as individual work.

## Three-layer AppSec workflow

VSH targets a developer-facing **L1 static detection → L2 LLM explanation → optional L3 proof-of-concept (PoC) generation and verification** workflow.

<picture>
  <source media="(max-width: 600px)" srcset="docs/assets/vsh-workflow-mobile.svg">
  <img src="docs/assets/vsh-workflow.svg" width="100%" alt="VSH three-stage AppSec workflow including LLM explanation and optional PoC validation">
</picture>

| Layer | Responsibility | Verified boundary |
| --- | --- | --- |
| **L1 — Detection** | Static analysis of code and dependencies through Semgrep and auxiliary rules | Real Semgrep execution integration and local fixture tests |
| **L2 — LLM explanation** | Explain risk, attack scenarios, and remediation using LLM/RAG context | Provider architecture is present; public demo explanations use mocks |
| **L3 — PoC generation and verification** | Optional PoC templates/generation path and controlled validation, supplemented by SonarQube/SBOM signals | End-to-end real PoC generation and execution remain unverified |

LLM explanations alone are not proof of exploitability, and unverified findings remain marked as candidates.

## Demo and verification

<p align="center"><img src="docs/assets/vsh-local-demo.png" width="100%" alt="VSH local security analysis and finding display"></p>

**Verified locally:** 81 tests and 81 reverse-order tests, plus a React production build (September 16, 2026). The team watcher targets a specific example file; MCP `apply_fix` returns proposed code but does not modify the source file. L2 public demo responses use mocks, and real L3 PoC execution remains unverified.


![VSH local fixture demo](docs/assets/vsh-local-demo.png)

*Actual local React UI and FastAPI fixture scan. Input: `tests/fixtures/vuln_project`; L2 explanation uses a **mock** provider; L3 is disabled. This does not establish actual LLM, SonarQube, PoC, or Electron packaged-app performance.* [Validation evidence](docs/portfolio-verification.md)

## Project at a glance

| Layer | Role | Scope |
| --- | --- | --- |
| L1 — Static findings | Source/dependency checks, including Semgrep integration | Findings are candidates for review |
| L2 — LLM explanations | Model/RAG-based risk rationale, attack scenarios, and remediation | Public fixture demo uses mock reasoning; real LLM quality is unverified |
| L3 — PoC generation & verification | Optional PoC templates and controlled validation, with SonarQube/SBOM supporting evidence | Real end-to-end PoC execution is not yet verified |
| Desktop and API | React/Electron front end, FastAPI runtime | Local prototyping |
| Finding v1.0 | Versioned output for downstream tools | Implemented; integrated dashboard is not yet available |

```mermaid
flowchart LR
  SRC["Source / Dependencies"] --> STATIC["L1: Static Checks"]
  STATIC --> REASON["L2: LLM Explanation / Annotation"]
  REASON --> OUT["Findings + Remediation"]
  STATIC -.-> VERIFY["Optional L3 PoC Generation + Validation"]
  VERIFY -.-> OUT
  OUT --> UI["React / Electron UI"]
```

## My contribution and verifiable changes

- **Semgrep executable integration and tooling/settings UX:** [commit](https://github.com/rasasoe/VSH/commit/ec15330c937432141ac62ae039c4b8f003f34546)
- **Windows Semgrep/Syft wrappers and local SonarQube configuration:** [wrapper](https://github.com/rasasoe/VSH/commit/0ec3f068e3402d1e4350990e5a4b51f03dd416d9) · [settings](https://github.com/rasasoe/VSH/commit/1a7e755e36cab8dafd6a0e40d1a392c0a74719be)
- **Finding v1.0 export, CLI output directory, contract tests and CI:** [PR #1](https://github.com/rasasoe/VSH/pull/1/files)
- **Architecture and evidence boundary documentation:** [README revision](https://github.com/rasasoe/VSH/commit/0f2f73c5ca6242f29926bf977edfa2d092050ab7)

## Recorded checks and limitations

At the **September 16, 2026** checkpoint: **81 unit tests passed**, the reverse-order test run passed **81**, and the React production build passed. The local fixture demonstrated findings and their not-verified status.

These checks **do not** prove exploitability, detection accuracy, live LLM quality, or production security. The three security tools (VSH, ASM, DotasPlus) can export normalized findings, but a shared operational dashboard is future work.

## Documentation and use

- [Full Korean documentation / 한국어 상세 문서](README.md) — installation, CLI, API, environment configuration and troubleshooting
- [Portfolio verification log](docs/portfolio-verification.md)
- [Upstream VSH](https://github.com/vmfmgl0607/VSH)

For reproducibility, use the setup and scope guidance in the Korean README and keep test targets authorized.

---

*VSH · Application Security Prototype · Upstream fork with independently documented extensions*
