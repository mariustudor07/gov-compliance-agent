# Git workflow (kept simple for a hackathon)

- `main` must always run. Nobody pushes straight to it.
- One branch per person/feature: `ai/classifier`, `scanner/cookies`, `frontend/report`, `db/scans`
- Commit small and often. Pull `main` into your branch before opening a PR.
- Open a PR, have someone else glance at it, then merge (squash merge is fine).
- Never commit `.env`, API keys, or the Mongo connection string.

```
git checkout main
git pull
git checkout -b scanner/cookies
# ...work...
git add -A
git commit -m "cookie check: detect pre-consent cookies"
git push -u origin scanner/cookies
# then open a PR on GitHub
```
