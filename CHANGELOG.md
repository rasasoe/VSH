# Changelog

## 2026-03-30

- cleaned up the repository to focus on runnable project assets
- moved active runtime DB storage to `C:\Users\<user>\.vsh\runtime_data`
- introduced runtime SQLite + Chroma bootstrap flow
- fixed Electron startup issues related to `ELECTRON_RUN_AS_NODE`
- cleaned up user-facing desktop UI text in key screens
- aligned desktop flow around Electron app usage instead of browser-only usage
- restored missing L3-related wiring pieces such as adapter/payload support paths
- added a demo-ready vulnerable fixture project for repeatable scans
- updated setup scripts and quick-start documentation
- expanded README and troubleshooting coverage for current project state

## Earlier integration work

- refactored active code paths toward clearer orchestration and runtime layers
- stabilized reporting and vulnerability flow handling
- kept compatibility wrappers so older imports would not break immediately
