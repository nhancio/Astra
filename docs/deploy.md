# Deploy from main

Commit your edits, then run from the repository:

```sh
./deploy.sh
```

The script:

1. Fetches origin, switches to `main`, merges origin/main and every local branch.
2. Validates the merged commit: deployment workflow checks, backend tests, a clean frontend install, production build and frontend checks. The frontend build generates both customer and admin artifacts.
3. Deletes local branches only after their commits are merged into main and validation passes.
4. Pushes main. Other remote branches are deleted only when their exact tip is already merged into main; conditional deletion rejects concurrent remote changes. Remote-only unmerged work stops deployment and is retained.
5. Confirms that main is the only local and remote branch, at the same commit. Builds and deploys from a frozen copy of that commit, checks the staged backend, activates it, then publishes both customer and admin Firebase Hosting targets.

Dirty files, unfinished Git operations, conflicts, rejected pushes and failed checks stop the script. It never force-pushes main or force-deletes a local branch. Branches checked out in other worktrees must be released there first. Failed merges are aborted; source branches remain available.

The existing Cloud SQL, server environment and IAM settings are retained. The release explicitly binds `ADMIN_API_KEY` to the latest version of the configured Secret Manager secret (default: `astra-admin-api-key`). Before promotion it checks that the admin overview rejects anonymous requests and accepts that secret, without printing the key. Failed admin checks stop traffic promotion and both website deployments. Local `.env` files are not uploaded or used to overwrite live configuration. Shared Redis is still a separate setup item. By default the smoke check allows only the known Redis-only 503 fallback, with an explicit warning, while PostgreSQL and access gates must pass. Set `REQUIRE_REDIS=1` to require HTTP 200 readiness with both dependencies healthy; any readiness failure then blocks promotion.

Required commands: Git, Python 3, npm, npx and gcloud, plus the installed backend virtual environment. HTTPS GitHub authentication uses the configured account's existing `gh` credential without changing the globally active account or writing the token to Git config. Other remote types use normal Git authentication.

Defaults:

| Variable | Default |
| --- | --- |
| `GITHUB_ACCOUNT` | `didigamnithin` |
| `FIREBASE_ACCOUNT` | `nithindidigam@nhancio.com` |
| `FIREBASE_PROJECT` | `yell-ai-nhancio` |
| `CLOUD_RUN_REGION` | `asia-south1` |
| `ADMIN_KEY_SECRET` | `astra-admin-api-key` (existing Secret Manager secret; deployer can read it and the Cloud Run identity can access it) |
| `REQUIRE_REDIS` | `0` (allow and warn about the existing local-memory fallback) |
| `BACKEND_PYTHON` | `backend/.venv/bin/python` |

Run the workflow regression checks without touching GitHub or Google Cloud:

```sh
python3 -m unittest discover -s tests -p test_deploy_workflow.py
```
