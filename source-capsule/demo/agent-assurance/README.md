# Agent assurance static demonstrator

This dependency-free page reads `data/report.json`, which is generated from the reviewed normalized fixtures by `interop/build_agent_assurance_report.py`.

It displays three independent axes:

- evidence finding;
- source processing state;
- applicability to a selected current revision.

The page does not execute Inspect AI, Promptfoo, an agent, or a model. Reproduce the underlying tool outputs with `interop/run_agent_assurance.sh`, then compare the normalized fixtures and generated report before changing this page. It is a repository demonstrator; no separate hosted Space or usability result is claimed.

The missing-observer view also compares the earlier generic adapter capability with the candidate per-case mapping. The earlier path did not establish a wrong real-world conclusion; it did not support this exact claim-specific observation contract. The comparison must preserve that boundary.

CPP Source Capsule is one technical component under exploration for the broader Open Agent Assurance Commons (OAAC) research direction. OAAC is not implemented by this page or repository.
