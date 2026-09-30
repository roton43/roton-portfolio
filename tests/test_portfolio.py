import json
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4

os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.gettempdir()) / f'portfolio-test-{uuid4().hex}.db')
os.environ['SESSION_SECRET'] = 'test-only-session-secret-with-more-than-32-characters'
os.environ['APP_ENV'] = 'development'
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
from app.security import hash_password
os.environ['ADMIN_PASSWORD_HASH'] = hash_password('test-password-only-12345')
from fastapi.testclient import TestClient
import pytest
from app.main import app, Session, Record, ProfileRow, seed, limiter
from sqlalchemy import delete


@pytest.fixture
def client():
    with TestClient(app) as c:
        with Session() as db:
            db.execute(delete(Record))
            db.execute(delete(ProfileRow))
            db.commit()
            seed(db)
        limiter.entries.clear()
        yield c


def token(response):
    return re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)


def login(client):
    page = client.get('/admin/login')
    result = client.post('/admin/login', data={'csrf': token(page), 'username': 'roton', 'password': 'test-password-only-12345'}, follow_redirects=False)
    assert result.status_code == 303
    return token(client.get('/admin'))


def post_data(csrf, visible=False):
    data = dict(csrf=csrf, slug='test-note', position='100', title='বাংলা test note', summary='A real test', date='2026-09-30', tags='Research', body='## Heading\n\nHello **world**. <script>alert(1)</script> [bad](javascript:alert(1))')
    if visible:
        data['published'] = 'on'
    return data


def test_all_public_routes_and_seed_counts(client):
    for path in ['/', '/work', '/research', '/about', '/blog', '/cv', '/work/netrolekha', '/health', '/sitemap.xml', '/feed.xml', '/robots.txt']:
        response = client.get(path)
        assert response.status_code == 200, path
    with Session() as db:
        papers = [r for r in db.query(Record).filter_by(kind='publication') if r.data['status'] == 'Published']
        assert len(papers) == 9
        assert sum(r.data['first_author'] for r in papers) == 1
    assert 'final result pending' in client.get('/about').text.lower()


def test_drafts_are_not_public(client):
    assert client.get('/blog/a-model-needs-a-system').status_code == 404
    assert 'a-model-needs-a-system' not in client.get('/sitemap.xml').text
    assert 'a-model-needs-a-system' not in client.get('/feed.xml').text
    assert 'First notes coming soon' in client.get('/blog').text


def test_unauthorized_admin_actions_cannot_write(client):
    for path in ['/admin', '/admin/backup', '/admin/profile', '/admin/edit/post/0']:
        assert client.get(path, follow_redirects=False).status_code == 303
    result = client.post('/admin/edit/post/0', data=post_data('fake', True), follow_redirects=False)
    assert result.status_code == 303
    assert client.get('/blog/test-note').status_code == 404


def test_csrf_rejected_and_login_rotates_token(client):
    initial = token(client.get('/admin/login'))
    assert client.post('/admin/login', data={'csrf': 'wrong'}).status_code == 403
    csrf = login(client)
    assert csrf != initial
    assert client.post('/admin/edit/post/0', data=post_data(initial, True)).status_code == 403
    assert client.post('/admin/profile', data={'csrf': 'fake'}).status_code == 403


def test_login_rate_limit(client):
    csrf = token(client.get('/admin/login'))
    for _ in range(5):
        assert client.post('/admin/login', data={'csrf': csrf, 'username': 'bad', 'password': 'bad'}).status_code == 401
    assert client.post('/admin/login', data={'csrf': csrf, 'username': 'roton', 'password': 'test-password-only-12345'}).status_code == 429


def test_publish_edit_delete_and_markdown_sanitization(client):
    csrf = login(client)
    assert client.post('/admin/edit/post/0', data=post_data(csrf, True), follow_redirects=False).status_code == 303
    response = client.get('/blog/test-note')
    assert response.status_code == 200 and '<strong>world</strong>' in response.text
    assert '<script>alert' not in response.text and 'href="javascript:' not in response.text
    assert 'test-note' in client.get('/sitemap.xml').text
    assert 'test-note' in client.get('/feed.xml').text
    with Session() as db:
        record_id = db.query(Record).filter_by(kind='post', slug='test-note').one().id
    data = post_data(csrf, False)
    assert client.post(f'/admin/edit/post/{record_id}', data=data, follow_redirects=False).status_code == 303
    assert client.get('/blog/test-note').status_code == 404
    assert client.post(f'/admin/delete/{record_id}', data={'csrf':csrf}, follow_redirects=False).status_code == 303
    with Session() as db:
        assert db.get(Record, record_id) is None


def test_preview_is_authenticated_and_sanitized(client):
    csrf = login(client)
    bad = '<img src=x onerror=alert(1)><iframe src="https://example.com"></iframe>\n\n## Safe'
    assert client.post('/admin/preview', json={'body': bad}).status_code == 403
    response = client.post('/admin/preview', json={'body': bad}, headers={'X-CSRF-Token':csrf})
    assert response.status_code == 200
    assert '<img' not in response.json()['html'] and '<iframe' not in response.json()['html']
    assert '<h2>Safe</h2>' in response.json()['html']


def test_duplicate_slugs_and_invalid_dates_preserve_database(client):
    csrf = login(client)
    data = post_data(csrf, True)
    assert client.post('/admin/edit/post/0', data=data, follow_redirects=False).status_code == 303
    assert client.post('/admin/edit/post/0', data=data).status_code == 422
    data['slug'] = 'different'
    data['date'] = 'not-a-date'
    assert client.post('/admin/edit/post/0', data=data).status_code == 422
    assert client.get('/blog/different').status_code == 404


def test_unsafe_profile_urls_rejected(client):
    csrf = login(client)
    with Session() as db:
        data = dict(db.get(ProfileRow, 1).data)
    data.update(csrf=csrf, github='javascript:alert(1)')
    assert client.post('/admin/profile', data=data).status_code == 422
    with Session() as db:
        assert db.get(ProfileRow, 1).data['github'] == 'https://github.com/roton43'


def test_backup_restore_is_atomic(client):
    csrf = login(client)
    backup = client.get('/admin/backup')
    assert backup.status_code == 200 and 'attachment' in backup.headers['content-disposition']
    data = backup.json()
    assert 'ADMIN_PASSWORD_HASH' not in backup.text
    original_name = data['profile']['name']
    data['profile']['name'] = 'Restore Test'
    data['records'][0]['data']['github'] = 'javascript:alert(1)'
    result = client.post('/admin/restore', data={'csrf':csrf,'confirm':'on'}, files={'backup':('backup.json',json.dumps(data),'application/json')})
    assert result.status_code == 422
    with Session() as db:
        assert db.get(ProfileRow, 1).data['name'] == original_name
    result = client.post('/admin/restore', data={'csrf':csrf,'confirm':'on'}, files={'backup':('backup.json',backup.content,'application/json')}, follow_redirects=False)
    assert result.status_code == 303


def test_seed_does_not_overwrite_edits_and_logout_revokes_session(client):
    csrf = login(client)
    with Session() as db:
        value = dict(db.get(ProfileRow, 1).data)
        value['headline'] = 'An updated headline'
        db.get(ProfileRow, 1).data = value
        db.commit()
        seed(db)
        assert db.get(ProfileRow, 1).data['headline'] == 'An updated headline'
    assert client.post('/admin/logout', data={'csrf':csrf}, follow_redirects=False).status_code == 303
    assert client.get('/admin', follow_redirects=False).status_code == 303


def test_security_headers_host_and_size_limits(client):
    response = client.get('/')
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert client.get('/admin/login').headers['cache-control'] == 'no-store'
    assert client.get('/', headers={'host':'evil.example'}).status_code == 400
    assert client.post('/admin/login', content=b'x'*2_000_001).status_code == 413


def test_production_refuses_ephemeral_sqlite(monkeypatch):
    from app.database import build_database
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:////tmp/never-use-this-in-production.db')
    with pytest.raises(RuntimeError, match='persistent PostgreSQL'):
        build_database()


def test_postgresql_connection_url_preserves_tls(monkeypatch):
    from app.database import database_url
    for prefix in ['postgres://', 'postgresql://', 'postgresql+psycopg://']:
        monkeypatch.setenv('DATABASE_URL', prefix + 'user:password@pool.example/db?sslmode=require&channel_binding=require')
        assert database_url() == 'postgresql+psycopg://user:password@pool.example/db?sslmode=require&channel_binding=require'


def test_code_blocks_preserve_quotes_and_literal_html():
    from app.main import render_markdown
    html = render_markdown('```python\nprint("hello")\n<script>example</script>\n```')
    assert 'print(&quot;hello&quot;)' in html
    assert '&amp;quot;' not in html
    assert '&lt;script&gt;example&lt;/script&gt;' in html
    assert '<script>' not in html
