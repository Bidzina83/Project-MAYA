Assistant GitHub App file-mod checklist

Purpose
- Store the exact, minimal sequence the assistant will use to modify/create files and open PRs with the provided GitHub App (APP_ID + PEM). This ensures future runs avoid host execution blocks.

Checklist (exact steps the assistant will execute)
1) Read credentials
   - Read APP_ID from argument or env.
   - Read PEM from /opt/data/.secrets/github-app/app.pem (do not print key).

2) Create JWT and installation token (single Python process)
   - Create JWT with RS256, short TTL (~10 minutes).
   - GET /repos/{owner}/{repo}/installation using Bearer JWT to get installation_id.
   - POST /app/installations/{installation_id}/access_tokens to get installation token.

3) Prepare branch
   - Ensure branch exists: GET ref heads/{branch}; if 404 create ref from base branch's sha.

4) Upload files & commit (prefer server-side Git objects)
   - For single-file edits: PUT /repos/{owner}/{repo}/contents/{path} (include sha if overwriting).
   - For multi-file batch: create blobs -> create tree (base_tree from head commit) -> create commit -> PATCH ref to new commit sha.

5) Create PR
   - POST /repos/{owner}/{repo}/pulls with title, head, base, body.

6) Error handling & host-block avoidance
   - Use only HTTP API calls (requests + PyJWT). Avoid spawning git/gh or shell here-docs.
   - On host-block or permission errors, stop attempts to run CLI and fall back to API-only blob/tree/commit flow.
   - Mask tokens in logs, retry ephemeral failures up to 3x with backoff.

7) Post-PR
   - Monitor Actions runs using installation token; download logs if requested.

Files & scripts to use
- Preferred helper: /opt/data/skills/mlops/persistent-memory-subsystem/scripts/pr_create_via_app.py
- Alternate helper: /opt/data/scripts/github_app_pr.py

Notes
- Do not persist installation tokens. Treat PEM as a secret and never print it.
- This checklist is authoritative for the assistant's behavior when modifying your repo.
