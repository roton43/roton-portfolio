import json
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, quote
from xml.sax.saxutils import escape

import bleach
import markdown
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select, text, delete
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .database import ROOT, Base, Record, ProfileRow, build_database
from .schemas import SCHEMAS, Profile, form_fields
from .security import authenticated, csrf_token, check_csrf, verify_password, admin_fingerprint, LoginLimiter

load_dotenv(ROOT / '.env')
PRODUCTION = os.getenv('APP_ENV') == 'production'
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000').rstrip('/')
SECRET = os.getenv('SESSION_SECRET') or secrets.token_urlsafe(48)
if PRODUCTION:
    if len(os.getenv('SESSION_SECRET', '')) < 32:
        raise RuntimeError('Production needs SESSION_SECRET with at least 32 characters.')
    if not os.getenv('ADMIN_PASSWORD_HASH', '').startswith('pbkdf2_sha256$'):
        raise RuntimeError('Set ADMIN_PASSWORD_HASH using python -m scripts.password.')
    if urlsplit(SITE_URL).scheme != 'https' or not urlsplit(SITE_URL).hostname:
        raise RuntimeError('Production SITE_URL must be your full HTTPS portfolio URL.')
    if not os.getenv('ALLOWED_HOSTS') or '*' in os.getenv('ALLOWED_HOSTS', ''):
        raise RuntimeError('Set ALLOWED_HOSTS to your actual domain, without https://.')

engine, Session = build_database()
templates = Jinja2Templates(directory=str(ROOT / 'app/templates'))
limiter = LoginLimiter()


def now():
    return datetime.now(timezone.utc).isoformat()


def render_markdown(source):
    html = markdown.markdown(source, extensions=['fenced_code', 'tables', 'sane_lists'])
    html = bleach.clean(html, tags=['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'pre', 'code', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'],
                        attributes={'a': ['href', 'title'], 'code': ['class']}, protocols=['https', 'mailto'], strip=True)
    return html


def seed(db):
    # Seed only a brand-new database. Never overwrite admin updates on redeploy.
    if db.get(ProfileRow, 1):
        return
    data = json.loads((ROOT / 'content/seed.json').read_text(encoding='utf-8'))
    db.add(ProfileRow(id=1, data=Profile.model_validate(data['profile']).model_dump()))
    for position, row in enumerate(data['records']):
        db.add(Record(kind=row['kind'], slug=row['slug'], published=row['published'],
                      position=row.get('position', position), updated_at=now(),
                      data=SCHEMAS[row['kind']].model_validate(row['data']).model_dump()))
    db.commit()


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with Session() as db:
        seed(db)
    yield
    engine.dispose()


app = FastAPI(title='Md. Roton Ahmed · Portfolio', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET, session_cookie='portfolio_session',
                   max_age=28800, same_site='lax', https_only=PRODUCTION)
hosts = [x.strip() for x in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') if x.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
app.mount('/static', StaticFiles(directory=str(ROOT / 'app/static')), name='static')


@app.middleware('http')
async def security_headers(request, call_next):
    if request.method == 'POST':
        size = request.headers.get('content-length', '')
        if not size.isdigit() or int(size) > 2_000_000:
            return JSONResponse({'detail': 'Request must include Content-Length and be under 2 MB.'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    if PRODUCTION:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    if request.url.path.startswith('/admin'):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response


def profile(db):
    return db.get(ProfileRow, 1).data


def rows(db, kind, public=True):
    query = select(Record).where(Record.kind == kind)
    if public:
        query = query.where(Record.published.is_(True))
    result = list(db.scalars(query.order_by(Record.position, Record.id)))
    if kind == 'post':
        result.sort(key=lambda row: row.data['date'], reverse=True)
    return result


def page(request, name, db, title='', description='', status=200, **extra):
    person = profile(db)
    skills = []
    for line in person['skills'].splitlines():
        if ':' in line:
            label, values = line.split(':', 1)
            skills.append({'label': label.strip(), 'items': [v.strip() for v in values.split(',') if v.strip()]})
    context = {'request': request, 'person': person, 'skills': skills,
               'title': title or f"{person['name']} · AI research & engineering",
               'description': description or person['summary'], 'site_url': SITE_URL,
               'canonical': SITE_URL + request.url.path, 'year': datetime.now().year,
               'active': request.url.path, 'admin': authenticated(request), **extra}
    if request.url.path.startswith('/admin'):
        context['csrf'] = csrf_token(request)
    return templates.TemplateResponse(request=request, name=name, context=context, status_code=status)


def require_admin(request):
    if not authenticated(request):
        raise HTTPException(303, headers={'Location': '/admin/login'})


def get_record(db, kind, slug):
    row = db.scalar(select(Record).where(Record.kind == kind, Record.slug == slug, Record.published.is_(True)))
    if row is None:
        raise HTTPException(404, 'This page is not available.')
    return row


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    if exc.status_code == 303:
        return RedirectResponse(exc.headers['Location'], status_code=303)
    if request.url.path.startswith('/admin/preview'):
        return JSONResponse({'detail': exc.detail}, status_code=exc.status_code)
    with Session() as db:
        return page(request, 'error.html', db, title=f'{exc.status_code} · Portfolio',
                    status=exc.status_code, code=exc.status_code, message=exc.detail)


@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    with Session() as db:
        pubs = rows(db, 'publication')
        published = [x for x in pubs if x.data['status'] == 'Published']
        return page(request, 'home.html', db,
                    projects=[p for p in rows(db, 'project') if p.data['featured']],
                    publications=published[:3], posts=rows(db, 'post')[:3],
                    publication_count=len(published), first_author_count=sum(x.data['first_author'] for x in published),
                    experiences=rows(db, 'experience'), awards=rows(db, 'award'))


@app.get('/work', response_class=HTMLResponse)
def work(request: Request, category: str = 'All'):
    if category not in {'All', 'Research', 'Engineering'}:
        category = 'All'
    with Session() as db:
        projects = rows(db, 'project')
        if category != 'All':
            projects = [x for x in projects if x.data['category'] == category]
        return page(request, 'work.html', db, title='Selected work · Md. Roton Ahmed', projects=projects, category=category)


@app.get('/work/{slug}', response_class=HTMLResponse)
def project_detail(request: Request, slug: str):
    with Session() as db:
        row = get_record(db, 'project', slug)
        return page(request, 'project.html', db, title=row.data['title'] + ' · Md. Roton Ahmed', description=row.data['summary'], item=row)


@app.get('/research', response_class=HTMLResponse)
def research(request: Request, status: str = 'All'):
    if status not in {'All', 'Published', 'Submitted', 'In preparation'}:
        status = 'All'
    with Session() as db:
        pubs = rows(db, 'publication')
        if status != 'All':
            pubs = [x for x in pubs if x.data['status'] == status]
        return page(request, 'research.html', db, title='Research & publications · Md. Roton Ahmed', publications=pubs, filter_status=status)


@app.get('/about', response_class=HTMLResponse)
def about(request: Request):
    with Session() as db:
        return page(request, 'about.html', db, title='About · Md. Roton Ahmed', experiences=rows(db, 'experience'), awards=rows(db, 'award'))


@app.get('/blog', response_class=HTMLResponse)
def blog(request: Request):
    with Session() as db:
        return page(request, 'blog.html', db, title='Field notes · Md. Roton Ahmed', posts=rows(db, 'post'))


@app.get('/blog/{slug}', response_class=HTMLResponse)
def post_detail(request: Request, slug: str):
    with Session() as db:
        row = get_record(db, 'post', slug)
        return page(request, 'post.html', db, title=row.data['title'] + ' · Md. Roton Ahmed', description=row.data['summary'], item=row, body=render_markdown(row.data['body']), reading_minutes=max(1, len(row.data['body'].split()) // 200))


@app.get('/cv', response_class=HTMLResponse)
def cv(request: Request):
    with Session() as db:
        return page(request, 'cv.html', db, title='CV · Md. Roton Ahmed', experiences=rows(db, 'experience'), awards=rows(db, 'award'), publications=rows(db, 'publication'), projects=rows(db, 'project'))


@app.get('/health')
def health():
    try:
        with Session() as db:
            db.execute(text('SELECT 1'))
        return {'status': 'ok'}
    except Exception:
        return JSONResponse({'status': 'unavailable'}, status_code=503)


@app.get('/robots.txt')
def robots():
    return Response(f'User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {SITE_URL}/sitemap.xml\n', media_type='text/plain')


@app.get('/sitemap.xml')
def sitemap():
    with Session() as db:
        paths = ['/', '/work', '/research', '/about', '/blog', '/cv']
        for kind, prefix in [('project', '/work/'), ('post', '/blog/')]:
            paths += [prefix + r.slug for r in rows(db, kind)]
        content = ''.join(f'<url><loc>{escape(SITE_URL + p)}</loc></url>' for p in paths)
    return Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + content + '</urlset>', media_type='application/xml')


@app.get('/feed.xml')
def feed():
    with Session() as db:
        p = profile(db)
        items = ''.join(f'<item><title>{escape(r.data["title"])}</title><link>{SITE_URL}/blog/{r.slug}</link><guid>{SITE_URL}/blog/{r.slug}</guid><description>{escape(r.data["summary"])}</description></item>' for r in rows(db, 'post'))
        xml = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{escape(p["name"])} · Field notes</title><link>{escape(SITE_URL)}/blog</link><description>Research and engineering notes</description>{items}</channel></rss>'
    return Response(xml, media_type='application/rss+xml')


@app.get('/admin/login', response_class=HTMLResponse)
def login_page(request: Request):
    if authenticated(request):
        return RedirectResponse('/admin', status_code=303)
    with Session() as db:
        return page(request, 'login.html', db, title='Sign in · Portfolio', error='')


@app.post('/admin/login')
async def login(request: Request):
    form = await request.form()
    check_csrf(request, form.get('csrf', ''))
    key = request.client.host if request.client else 'unknown'
    if not limiter.allow(key):
        with Session() as db:
            return page(request, 'login.html', db, title='Sign in · Portfolio', error='Too many attempts. Please wait 15 minutes.', status=429)
    stored = os.getenv('ADMIN_PASSWORD_HASH', '')
    if not stored:
        with Session() as db:
            return page(request, 'login.html', db, error='Admin access is not configured. Follow the setup guide to set your password.', status=503)
    valid_user = secrets.compare_digest(str(form.get('username', '')), os.getenv('ADMIN_USERNAME', 'roton'))
    valid_pass = verify_password(str(form.get('password', '')), stored)
    if not valid_user or not valid_pass:
        with Session() as db:
            return page(request, 'login.html', db, error='The username or password is incorrect.', status=401)
    limiter.clear(key)
    request.session.clear()
    request.session.update({'admin': admin_fingerprint(), 'expires': time.time() + 28800, 'csrf': secrets.token_urlsafe(32)})
    return RedirectResponse('/admin', status_code=303)


@app.post('/admin/logout')
async def logout(request: Request):
    require_admin(request)
    form = await request.form()
    check_csrf(request, form.get('csrf', ''))
    request.session.clear()
    return RedirectResponse('/admin/login', status_code=303)


@app.get('/admin', response_class=HTMLResponse)
def dashboard(request: Request, saved: str = ''):
    require_admin(request)
    with Session() as db:
        return page(request, 'admin.html', db, title='Content studio · Portfolio', groups={k: rows(db, k, False) for k in SCHEMAS}, saved=bool(saved))


@app.get('/admin/profile', response_class=HTMLResponse)
def edit_profile(request: Request):
    require_admin(request)
    with Session() as db:
        return page(request, 'editor.html', db, title='Edit profile · Portfolio', editing_profile=True, kind='profile', fields=form_fields(Profile), values=profile(db), errors=[], row=None)


@app.post('/admin/profile')
async def save_profile(request: Request):
    require_admin(request)
    form = await request.form()
    check_csrf(request, form.get('csrf', ''))
    values = {name: str(form.get(name, '')) for name in Profile.model_fields}
    with Session() as db:
        try:
            validated = Profile.model_validate(values).model_dump()
        except ValidationError as e:
            return page(request, 'editor.html', db, status=422, editing_profile=True, kind='profile', fields=form_fields(Profile), values=values, errors=[f'{x["loc"][0]}: {x["msg"]}' for x in e.errors()], row=None)
        db.get(ProfileRow, 1).data = validated
        db.commit()
    return RedirectResponse('/admin?saved=1', status_code=303)


def schema_for(kind):
    if kind not in SCHEMAS:
        raise HTTPException(404, 'Unknown content type.')
    return SCHEMAS[kind]


@app.get('/admin/edit/{kind}/{record_id}', response_class=HTMLResponse)
def edit_record(request: Request, kind: str, record_id: int):
    require_admin(request)
    schema = schema_for(kind)
    with Session() as db:
        row = db.get(Record, record_id) if record_id else None
        if record_id and (row is None or row.kind != kind):
            raise HTTPException(404, 'Content not found.')
        values = dict(row.data) if row else {name: '' for name in schema.model_fields}
        if not row:
            values.update({'date': datetime.now(timezone.utc).date().isoformat(), 'year': datetime.now().year, 'status': 'In preparation', 'category': 'Engineering'})
        return page(request, 'editor.html', db, title='Edit content · Portfolio', editing_profile=False, kind=kind, fields=form_fields(schema), values=values, row=row, errors=[], slug=row.slug if row else '', position=row.position if row else 100, published=row.published if row else False)


@app.post('/admin/edit/{kind}/{record_id}')
async def save_record(request: Request, kind: str, record_id: int):
    require_admin(request)
    schema = schema_for(kind)
    form = await request.form()
    check_csrf(request, form.get('csrf', ''))
    values = {name: form.get(name, False if field.annotation is bool else '') for name, field in schema.model_fields.items()}
    slug = str(form.get('slug', '')).strip()
    published = form.get('published') == 'on'
    position_text = str(form.get('position', '100'))
    errors = []
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or len(slug) > 160:
        errors.append('Slug: use lowercase English letters, digits and hyphens; maximum 160 characters.')
    try:
        position = int(position_text)
        if not 0 <= position <= 10000:
            raise ValueError()
    except ValueError:
        position = 100
        errors.append('Display order must be a number from 0 to 10000.')
    try:
        validated = schema.model_validate(values).model_dump()
    except ValidationError as e:
        errors += [f'{x["loc"][0]}: {x["msg"]}' for x in e.errors()]
    with Session() as db:
        row = db.get(Record, record_id) if record_id else None
        if record_id and (row is None or row.kind != kind):
            raise HTTPException(404, 'Content not found.')
        if not errors:
            if row is None:
                row = Record(kind=kind)
                db.add(row)
            row.slug, row.position, row.published, row.data, row.updated_at = slug, position, published, validated, now()
            try:
                db.commit()
                return RedirectResponse('/admin?saved=1', status_code=303)
            except IntegrityError:
                db.rollback()
                errors.append('This slug is already used. Choose another slug.')
        return page(request, 'editor.html', db, status=422, editing_profile=False, kind=kind, fields=form_fields(schema), values=values, row=row if record_id else None, errors=errors, slug=slug, position=position, published=published)


@app.post('/admin/delete/{record_id}')
async def delete_record(request: Request, record_id: int):
    require_admin(request)
    form = await request.form()
    check_csrf(request, form.get('csrf', ''))
    with Session() as db:
        row = db.get(Record, record_id)
        if row is None:
            raise HTTPException(404, 'Content not found.')
        db.delete(row)
        db.commit()
    return RedirectResponse('/admin?saved=1', status_code=303)


@app.post('/admin/preview')
async def preview_markdown(request: Request):
    require_admin(request)
    check_csrf(request, request.headers.get('x-csrf-token', ''))
    data = await request.json()
    if not isinstance(data, dict) or not isinstance(data.get('body'), str) or len(data['body']) > 100000:
        raise HTTPException(422, 'Markdown must be text under 100000 characters.')
    return {'html': render_markdown(data['body'])}


@app.get('/admin/backup')
def backup(request: Request):
    require_admin(request)
    with Session() as db:
        data = {'format': 1, 'exported_at': now(), 'profile': profile(db), 'records': [{'kind': r.kind, 'slug': r.slug, 'data': r.data, 'published': r.published, 'position': r.position} for r in db.scalars(select(Record).order_by(Record.id))]}
    return JSONResponse(data, headers={'Content-Disposition': 'attachment; filename="portfolio-backup.json"'})


@app.post('/admin/restore')
async def restore(request: Request):
    require_admin(request)
    form = await request.form()
    check_csrf(request, form.get('csrf', ''))
    if form.get('confirm') != 'on':
        raise HTTPException(422, 'Confirm replacement of current content first.')
    file = form.get('backup')
    try:
        data = json.loads(await file.read(2_000_001))
        if data.get('format') != 1 or not isinstance(data['records'], list) or len(data['records']) > 2000:
            raise ValueError('Invalid backup format')
        person = Profile.model_validate(data['profile']).model_dump()
        entries = []
        seen = set()
        for entry in data['records']:
            kind, slug = entry['kind'], entry['slug']
            if kind not in SCHEMAS or not isinstance(slug, str) or len(slug) > 160 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or (kind, slug) in seen:
                raise ValueError('Invalid or duplicate content')
            if type(entry['published']) is not bool or type(entry['position']) is not int or not 0 <= entry['position'] <= 10000:
                raise ValueError('Invalid content visibility or order')
            seen.add((kind, slug))
            entries.append(Record(kind=kind, slug=slug, data=SCHEMAS[kind].model_validate(entry['data']).model_dump(), published=entry['published'], position=entry['position'], updated_at=now()))
    except (AttributeError, KeyError, ValueError, TypeError, ValidationError):
        raise HTTPException(422, 'Invalid backup. Nothing was changed. Use an export from this portfolio.')
    with Session() as db:
        db.execute(delete(Record))
        db.get(ProfileRow, 1).data = person
        db.add_all(entries)
        db.commit()
    return RedirectResponse('/admin?saved=1', status_code=303)


# Template helpers never accept arbitrary executable HTML from editable content.
templates.env.filters['tags'] = lambda value: [x.strip() for x in value.split(',') if x.strip()]
templates.env.filters['doi_url'] = lambda value: 'https://doi.org/' + quote(value, safe='/._-')
