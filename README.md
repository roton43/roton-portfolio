# Md. Roton Ahmed — research & engineering portfolio

A complete, server-rendered FastAPI portfolio with an authenticated content studio, project case studies, publications, a Markdown blog, printable CV, PostgreSQL support and Docker deployment files.

**বাংলা নির্দেশনা:** [শুরু করো এখানে](docs/START_HERE_BN.md) → [Free deployment](docs/DEPLOYMENT_BN.md) → [Content update ও blog](docs/CONTENT_GUIDE_BN.md).

## Included

- Responsive home, work, research, about and blog pages.
- Nine published conference papers: eight coauthored and one first-authored, with DOI links.
- Three manuscript entries with distinct publication statuses.
- Nine project case studies, including NetroLekha, handwriting collection, a ViT MRI classifier and an inference API.
- Admin CRUD for projects, publications, posts, experience and awards; profile and links editor.
- Private drafts, Markdown preview, Bengali/English writing, RSS and sitemap.
- Content export and validated atomic restore.
- A current printable CV generated from editable content.
- Local SQLite, Docker Compose with PostgreSQL and a Render Docker Blueprint.

## Quick local setup

Use Python 3.12. Commands are run from this folder.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m scripts.password
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated password hash and secret in `.env` as described in [START_HERE_BN.md](docs/START_HERE_BN.md). There is **no default admin password**. Start the site:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000` and `http://localhost:8000/admin/login`.

## Docker

After creating `.env`:

```bash
docker compose up --build -d
docker compose logs -f web
```

The Compose configuration uses a PostgreSQL volume and exposes only the web service on local port 8000. The development database credential in Compose is intentionally local-only; it is not used by production deployment.

To run a single container against an external database:

```bash
docker build -t roton-portfolio .
docker run --rm --env-file .env -p 127.0.0.1:8000:8000 roton-portfolio
```

For this single-container command, set `DATABASE_URL` to an external PostgreSQL URL. Use Compose for a persistent local database.

## Free hosting

The deployment target is **Render Free Docker Web Service + Neon Free PostgreSQL**, not Render's expiring free database. Follow [DEPLOYMENT_BN.md](docs/DEPLOYMENT_BN.md).

**Live portfolio:** https://roton-portfolio.onrender.com/  
**Content studio:** https://roton-portfolio.onrender.com/admin/login

Deployed and verified on 30 September 2026 using Render Free Docker and Neon Free PostgreSQL in Singapore. Admin login, Markdown preview, saving a private draft and persistence across a Render redeploy passed. GitHub `main` commits trigger automatic deployment; studio content edits appear immediately without a deploy. Free hosting has quotas and cold starts.

The studio username is `roton`. Sign in with the original password chosen when generating the hash. The hash belongs only in `ADMIN_PASSWORD_HASH`; it is not the login password. Email credentials are not portfolio credentials.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --check app/static/site.js
```

Node is only needed for the optional JavaScript syntax check; the application does not need Node or a frontend build step.

## Structure

| Path | Purpose |
| --- | --- |
| `app/main.py` | Public pages, admin actions, feeds and security headers |
| `app/database.py` | SQLAlchemy database models and connection configuration |
| `app/schemas.py` | Content validation and editor fields |
| `app/security.py` | Password hashing, sessions, CSRF and login limiting |
| `app/templates/` | Jinja templates for public and admin pages |
| `app/static/` | Responsive CSS, small JavaScript interactions and favicon |
| `content/seed.json` | Initial verified content; used only on an empty database |
| `scripts/password.py` | Interactive password-hash generation |
| `Dockerfile`, `compose.yaml` | Container runtime and local PostgreSQL setup |
| `render.yaml` | Free Render Docker service configuration |
| `tests/` | Functional and security regression checks |
| `docs/` | Setup, deployment, editing, sources and verification |

## Content accuracy

The user's latest education and manuscript-status instructions override older CV statements. Final CGPA is omitted while the result is pending. Original CV PDFs, private datasets, telephone numbers and referee contact details are not served by this application. See [SOURCES.md](docs/SOURCES.md) for provenance and remaining confirmation items.

## Maintenance

Back up content regularly from `/admin`. Keep credentials in `.env` locally and in the hosting dashboard for deployment. Never commit them. The schema is created automatically on first boot; seed data never overwrites existing edits. Future schema changes need an explicit migration plan before deployment—`create_all()` does not alter existing tables.

Changing templates, CSS or Python requires a repository commit and redeploy. Editing portfolio content or blog posts through the studio takes effect immediately without redeployment.
