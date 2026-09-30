# Verification and practical limits

Checked on 30 September 2026 using Python 3.12 and the package versions in `requirements.txt`. This records what was actually checked, rather than implying external hosting was exercised.

## Automated application tests

Run `python -m pytest -q` from the project root after installing `requirements-dev.txt`.

- Public routes and initial paper counts: nine published, one first-author.
- Draft exclusion from public pages, RSS and sitemap.
- Unauthorized admin reads/writes blocked.
- CSRF protection and token rotation at login.
- Login-attempt limiting.
- Blog creation, publishing, unpublishing and deletion.
- Markdown sanitation of scripts, unsafe links, images and iframes.
- Authenticated preview endpoint and correctly escaped code examples.
- Duplicate slugs and invalid dates rejected without saving invalid data.
- Unsafe profile links rejected.
- Backup export and validated atomic restore.
- Initial seed preserves existing database edits.
- Logout returns the browser to unauthenticated state.
- Content security policy, no-store admin headers, host validation and request-size limits.
- Production configuration refuses ephemeral SQLite.
- PostgreSQL driver normalization preserves TLS connection parameters.

The suite has **15 tests**. TestClient may emit a dependency deprecation notice about `httpx`; this does not affect the application's runtime.

## Browser checks

Chromium checked public routes at **1440px**, **390px** and **320px** viewport widths. No horizontal overflow was found on the checked pages. Mobile menu navigation, research-status filters, project-category filters and browser CV printing passed.

The admin browser flow used a disposable database: sign in → new Bengali/English Markdown post → sanitized preview → private draft → publish → inspect article → delete → sign out. No browser JavaScript errors remained after the fixes. A self-hosted Noto Sans Bengali font was checked in the browser, and quoted code examples were verified against the rendered text.

Screenshots in `docs/preview/` show the home page, mobile home page, content studio and article editor. The editor screenshot shows the included private sample outline, not a published owner article.

JavaScript syntax check, Python compilation and `pip check` passed.

## Not executed here

- Docker is unavailable in the execution environment, so `docker build` / `docker compose up` were not run. Dockerfile and Compose configuration were reviewed; owner-side build steps are in the guide.
- A live PostgreSQL / Neon connection was not available. Functional tests use a temporary SQLite database; production PostgreSQL configuration and connection-string handling are included and checked, but a live database smoke test is still required during deployment.
- No GitHub repository was created or pushed, and no Render/Neon resources were created in the owner's accounts.
- No paid plans, domains or hosting purchases were made.

## Deployment checks to perform

Follow `DEPLOYMENT_BN.md`, including `/health`, admin login, save/publish and redeploy-persistence checks against Neon. Free hosting adds cold-start delays, quotas and availability limits. Do not present this release as a tested always-on hosted service.

## Implementation notes

- Server-rendered FastAPI/Jinja application; no frontend build step.
- Signed HttpOnly admin session cookies with an eight-hour lifetime, Secure in production, SameSite=Lax and CSRF-protected writes.
- Passwords use salted PBKDF2-SHA256 hashes; no default admin credential.
- Stored data is validated before writes; public Markdown is sanitized before rendering.
- The login limiter is deliberately single-worker and in memory. Use one Uvicorn worker as configured. A larger deployment should use a shared limiter before scaling across workers or instances.
- No files are uploaded to the host for public content; hosted content is kept in PostgreSQL. Backup restore accepts JSON content only.
- `create_all()` creates the initial schema but does not migrate existing tables. Future schema changes require explicit migrations.
- The curated CV is a printable HTML page. Original attached CV files are not publicly hosted.
- Blog supports manual publishing, without scheduling or media uploads in this release.
