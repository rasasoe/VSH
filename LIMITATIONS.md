# LIMITATIONS

- L1 is still primarily a fast heuristic and rule-driven layer, not a full program-analysis engine.
- L2 can run in mock mode and is not guaranteed to use a real provider unless API keys are configured.
- L3 remains dependency-gated and is not fully active in base setup without Sonar and related tooling.
- Some repository and class names still reflect older mock-era naming even though the runtime path now uses real runtime DBs.
- Compatibility wrappers and legacy paths still exist to reduce breakage, so the codebase is not yet fully consolidated.
- Some non-user-facing source files still contain legacy comments or encoding artifacts that do not affect the main product flow.
- Syft-based dependency analysis is optional and not bundled automatically at the OS level.
- The desktop app is currently run from source rather than from a packaged installer.
