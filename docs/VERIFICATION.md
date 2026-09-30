# Verification and practical limits

Checked on 30 September 2026 using Python 3.12 and the package versions in `requirements.txt`. Both local application checks and the live Render/Neon deployment were exercised.

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

## Live deployment checks

- Public source is in https://github.com/roton43/roton-portfolio; Render deploys the `main` branch automatically.
- https://roton-portfolio.onrender.com/ runs the Dockerfile on a Render Free web service in Singapore, connected to Neon Free PostgreSQL in Singapore. The Docker build, startup and health checks succeeded on Render.
- Eleven HTTPS routes returned 200: `/health`, `/`, `/work`, `/research`, `/about`, `/blog`, `/cv`, `/admin/login`, `/robots.txt`, `/sitemap.xml` and `/feed.xml`. Health returned `{"status":"ok"}`.
- Security response checks included `nosniff`, admin `no-store`/`noindex`, and sitemap links using the live hostname.
- Live Neon contained nine projects, twelve publication records (nine published plus three manuscripts), five experience records, three awards and one private blog draft.
- The owner's admin login succeeded. The live editor rendered a Bengali/English Markdown preview and saved a private draft.
- A temporary marker saved in that draft remained visible in the editor and Neon after a Render redeploy completed. The authenticated session also remained usable. The original draft text was restored afterwards and the marker was confirmed absent; HTML form submission normalizes its line endings to CRLF.
- The private draft detail returned 404 to an unauthenticated request and was absent from RSS and sitemap. The example remains unpublished.
- Live public publishing/deletion and production backup restore were not exercised; those flows passed against the disposable local test database.

## Practical limits

- Local Docker/Compose executables are unavailable, so local `docker build` / `docker compose up` were not run. The production Docker image was built and deployed successfully by Render; the local Compose workflow remains owner-run.
- No paid plans, domains or hosting purchases were made.
- Free hosting adds cold-start delays, quotas and availability limits; this is not an always-on uptime guarantee. See `DEPLOYMENT_BN.md` for ongoing maintenance and backups.

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
