---
name: defect-discovery
description: Systematically discover latent defects in code with a behavior-tracing audit procedure. Use when the user asks for a code audit, a full audit, a diff review, or a check for latent defects (state transitions, races, persistence, numerics, unbounded growth, idempotency). Applies a common core (Steps 0-7: behavior tracing, mechanical enumeration, defect-class matrix, independent multi-pass union with skeptical re-review, dynamic verification, invariants, on-the-spot registration, reporting format) plus Mode 1 (diff review) or Mode 2 (full-codebase inspection). The procedure itself is in English in defect-discovery-skill.en.md; reports to the user are written in Japanese. Do not use a passing audit as evidence that no deep defects exist; state which methods were not used and what remains unverified.
license: MIT
metadata:
  author: Chisiki1
  source: https://github.com/Chisiki1/muse-agent-operations-kit
  commit: e9e4ec01362b627092fa08539742daa798dc3fdb
  source_file: defect-discovery-skill.en.md
---

# Defect Discovery (Code Audit)

Read `defect-discovery-skill.en.md` in this directory and follow its procedure when the user asks for a code audit, a diff review, or a full-codebase inspection.

- Declare which mode applies at the start: Mode 1 (diff review) or Mode 2 (full-codebase inspection). Apply the common core (Steps 0–7) together with that mode's section.
- The main axis is tracing behavior (Step 0): for each change, trace forward through its connections to unchanged code and ask how the change alters the behavior of the assembled system. The defect-class matrix (Step 2) is an auxiliary sweep afterwards, not the definition of coverage.
- Keep the audit ledger as the procedure requires: population definition, understanding scope per range, enumeration output, dispositions per enumerated target, findings with severities, methods used and not used, static vs. dynamically demonstrated findings, and the unverified range.
- A finding is registered the moment a divergence from the contract is identified; impact evaluation goes in the disposition field only and never rewrites the existence judgment into "no problem".
- Report to the user in Japanese, following the reporting format in the procedure file. State explicitly which methods were not used and what remains unverified.
- This skill is for general defect classes. It is separate from security auditing (CWE-specific).
- The operations kit in the same repository (muse-agent-operations-kit.md, self-improvement loops and other operating mechanisms) is NOT adopted; only this defect-discovery procedure is installed.
