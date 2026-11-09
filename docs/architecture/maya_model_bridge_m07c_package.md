# M07c Offline Package

2026-11-03. Assembly approved for M07c only, including omission of only
model_oversized_child_entry.py and model_oversized_worker_entry.py from the new
payload. Canonical helpers and predecessor packages remain unchanged.

This case changes one fixture-content byte in otherwise valid JSON. The original
exact-byte comparison must reject it after size and JSON checks. Expect one
synthetic dispatch, two audit records, and zero model deliveries or publications.

Extract into a fresh guest folder and report the executable path and SHA256.
Do not launch until separate exact-artifact one-run approval and fresh consent.
No VM setup, security changes, inference, retries, or qualification.
