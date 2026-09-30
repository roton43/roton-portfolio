# Free deployment: Render + Neon

এই guide FastAPI ও Docker application-টি public internet-এ চালানোর জন্য। যাচাইয়ের তারিখ: **৩০ সেপ্টেম্বর ২০২৬**। Free-plan rules পরে বদলাতে পারে; service তৈরির সময় dashboard-এ `Free` নির্বাচন করো এবং কোনো paid upgrade enable করবে না যদি zero-cost রাখতে চাও।

## তোমার live setup

- **Portfolio:** https://roton-portfolio.onrender.com/
- **Admin:** https://roton-portfolio.onrender.com/admin/login
- **Source:** https://github.com/roton43/roton-portfolio
- **Hosting:** Render Free Docker + Neon Free PostgreSQL; দুটোই Singapore region।
- **Login:** username `roton`, এবং hash তৈরি করার সময় নিজের বেছে নেওয়া original password। Login form-এ hash বা email password দেবে না।

Deployment, health check, public pages, admin login, Markdown preview এবং private draft save যাচাই হয়েছে। Render redeploy-এর পর draft database-এ অক্ষত ছিল; draft public page-এ 404 এবং RSS/sitemap-এ অনুপস্থিত ছিল। পরীক্ষার temporary লেখা সরিয়ে original draft ফিরিয়ে দেওয়া হয়েছে। GitHub `main`-এর জন্য auto-deploy enabled আছে। নিচের ধাপগুলো local setup বা ভবিষ্যতে deployment পুনরায় করার reference।

## এই setup কেন

| অংশ | Service | কাজ |
| --- | --- | --- |
| Application | Render Free Web Service, Docker runtime | FastAPI website ও admin |
| Database | Neon Free PostgreSQL | Profile, projects, publications ও blog স্থায়ীভাবে রাখা |
| Source | তোমার GitHub repository | Code versioning ও deploy trigger |
| URL | Render-এর দেওয়া `*.onrender.com` | HTTPS public portfolio address |

Render Free web service ১৫ মিনিট idle থাকলে sleep করে; পরের request-এ startup প্রায় এক মিনিট লাগতে পারে। Local files restart/redeploy-এ হারায়। তাই hosted content PostgreSQL-এ থাকে। Render-এর free PostgreSQL ৩০ দিন পরে expire করে, তাই এই project-এ সেই database বেছে নেওয়া হয়নি।

Neon-এর বর্তমান Free plan-এ ০.৫ GB database storage per project এবং monthly compute quota রয়েছে। এটি ছোট portfolio-র জন্য practical starting point, তবে free hosting-এ always-on uptime guarantee নেই। Custom domain চাইলে domain কেনার খরচ আলাদা।

## ১. Code GitHub-এ রাখো

তোমার GitHub account-এ নতুন repository তৈরি করো, যেমন `roton-portfolio`। এটি public বা private—দুটোই হতে পারে। Terminal-এ project folder থেকে:

```bash
git init
git add .
git commit -m "Build research and engineering portfolio"
git branch -M main
git remote add origin https://github.com/roton43/roton-portfolio.git
git push -u origin main
```

Repository URL: `https://github.com/roton43/roton-portfolio`। এই repository-তে project source upload করা হয়েছে। `.env`, local database ও backups `.gitignore`-এ আছে। `.env` কখনো force-add করবে না।

## ২. Neon Free database তৈরি করো

1. [Neon](https://neon.com/) account-এ sign in করো।
2. Free plan-এ নতুন project তৈরি করো; নাম `roton-portfolio` রাখতে পারো।
3. PostgreSQL database তৈরি হলে **Connect** থেকে connection string নাও।
4. **Pooled connection** নির্বাচন করো এবং TLS parameters রাখো। সাধারণ format:

```text
postgresql://USER:PASSWORD@YOUR-POOLED-HOST/DBNAME?sslmode=require
```

Actual Neon string-এ `channel_binding=require` বা অন্য parameter থাকলে সেটিও রাখবে। Application নিজে driver prefix ঠিক করে নেয়। Password-এ special character থাকলে Neon-এর দেওয়া encoded connection string-ই ব্যবহার করো।

এই string private credential। GitHub, blog বা public chat-এ paste করবে না। Render-এর `DATABASE_URL` secret হিসেবে বসাবে।

## ৩. Render service তৈরি করো

1. [Render Dashboard](https://dashboard.render.com/)-এ sign in করো।
2. **New → Web Service** নির্বাচন করো।
3. নিজের GitHub account connect করে `roton-portfolio` repository নির্বাচন করো।
4. Branch `main`; Root Directory খালি, কারণ project files repository root-এ থাকবে।
5. Language/Runtime **Docker**; Dockerfile Path `./Dockerfile`।
6. Instance Type **Free**।
7. Health Check Path `/health`।
8. Docker Command খালি রাখো; project-এর Dockerfile startup command ব্যবহার করবে।

### Required environment variables

| Variable | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Neon-এর actual pooled PostgreSQL string |
| `SESSION_SECRET` | কমপক্ষে ৩২-character random secret; local generator ব্যবহার করো |
| `ADMIN_USERNAME` | নিজের chosen username, যেমন `roton` |
| `ADMIN_PASSWORD_HASH` | `python -m scripts.password`-এ তৈরি সম্পূর্ণ hash |
| `SITE_URL` | Actual full HTTPS URL, যেমন `https://roton-portfolio.onrender.com` |
| `ALLOWED_HOSTS` | URL-এর hostname only, যেমন `roton-portfolio.onrender.com` |

Render environment field-এ hash বসানোর সময় `.env`-এর surrounding quotes বসাবে না; actual hash value বসাবে। `ALLOWED_HOSTS`-এ `https://` বা path বসাবে না। একাধিক actual domain হলে comma দিয়ে আলাদা করো। Docker internal healthcheck-এর জন্য `127.0.0.1`-ও যোগ করতে পারো, যেমন `roton-portfolio.onrender.com,127.0.0.1`।

Admin password নিজে বেছে নিতে project folder থেকে `python -m scripts.password` চালাও। এই hash utility Python standard library দিয়েই চলে, application dependencies আগে install করতে হয় না। Password terminal-এ লুকানো থাকবে। Render-এর `ADMIN_PASSWORD_HASH` field-এ output-এর `pbkdf2_sha256$...` অংশ বসাবে; `ADMIN_PASSWORD_HASH=` prefix দেবে না।

Render তৈরি করা actual URL নামের availability অনুযায়ী বদলাতে পারে। Dashboard-এর actual URL ব্যবহার করবে। URL প্রথম deploy-এর পরে নিশ্চিত হলে environment-এ `SITE_URL` ও `ALLOWED_HOSTS` সংশোধন করে redeploy করো। Required production config অসম্পূর্ণ থাকলে application ইচ্ছাকৃতভাবে startup বন্ধ করে।

**Deploy Web Service** চাপো। Render repository থেকে Docker image build করে application start করবে। প্রথম boot-এ tables ও seed content তৈরি হবে। পরের redeploy-এ PostgreSQL-এর updates থাকবে।

## ৪. Blueprint বিকল্প

Manual Web Service তৈরির বদলে **New → Blueprint** থেকে একই repository connect করলে `render.yaml` পড়বে। শুধু `ADMIN_PASSWORD_HASH` ও `DATABASE_URL` নিজের values দিয়ে বসাবে। `SESSION_SECRET` Render generate করবে; `SITE_URL` ও `ALLOWED_HOSTS` একই service-এর actual Render URL ও hostname থেকে স্বয়ংক্রিয়ভাবে আসবে। Free plan, Singapore region, Docker runtime ও health path file-এ দেওয়া আছে। Neon database আলাদাভাবে তৈরি করবে।

এই deployed service-এ **auto-deploy enabled** আছে: GitHub `main`-এ commit/push হলে Render নতুন deployment শুরু করবে। Push-এর পরে আলাদা manual deploy দেওয়ার দরকার নেই। অন্য service-এ auto-deploy বন্ধ থাকলে Dashboard থেকে manual deploy করবে। Blog ও content update-এর জন্য redeploy দরকার হয় না।

## ৫. Deploy যাচাই করো

Actual URL-এ:

1. `/health` → `{"status":"ok"}`।
2. Home, research ও project pages খোলো।
3. `/admin/login`-এ নিজের credentials দিয়ে sign in করো।
4. একটি private draft blog লিখে save করো; logged-out browser-এ সেই URL unavailable হবে।
5. লেখাটি publish করলে blog list ও detail page-এ দেখা যাবে।
6. Admin থেকে backup download করো।
7. Render redeploy করে profile ও blog changes রয়ে গেছে কি না দেখো।
8. Mobile browser-এ menu, project links ও email link যাচাই করো।

## ৬. Updates

- **Blog/content:** `/admin`-এ edit ও save; সঙ্গে সঙ্গে website update হয়।
- **Code/design:** GitHub-এ commit/push; Render auto-deploy enabled থাকলে নতুন deployment শুরু হয়।
- **CV:** `/cv` page বর্তমান content দেখায়। `Save as PDF / Print CV` থেকে PDF save করো।
- **Password:** নতুন hash generate করে Render environment-এ replace ও redeploy করো। পুরোনো signed sessions নতুন hash-এর সঙ্গে মিলবে না।

## ৭. Backup ও restore

নিয়মিত `/admin`-এর **Download content backup** ব্যবহার করো। JSON-এ drafts-ও থাকে, তাই backup private রাখবে। Restore একই studio থেকে হয় এবং current profile ও সব content replace করে। Invalid backup হলে কোনো পরিবর্তন হয় না।

Local SQLite-এ করা initial custom edits যদি Neon-এ নিতে চাও: local admin থেকে JSON export করো, hosted admin-এ sign in করে restore করো। শুধু `seed.json` বদলে existing database-এ redeploy করলে content overwrite হবে না।

## Common problems

| সমস্যা | করণীয় |
| --- | --- |
| প্রথম visit-এ loading page | Free service-এর cold start শেষ হওয়ার জন্য অপেক্ষা করো |
| `Invalid host header` | Actual hostname `ALLOWED_HOSTS`-এ বসাও |
| Production database error | Neon string, password ও TLS parameters যাচাই করো; SQLite ব্যবহার করবে না |
| Admin disabled locally | `.env`-এ generated password hash বসাও; server restart করো |
| Production startup secret error | কমপক্ষে ৩২-character `SESSION_SECRET` বসাও |
| Login form expired | Page reload করে আবার sign in করো |
| Username/password ভুল | Username `roton`; hash তৈরির সময় বেছে নেওয়া original password দাও। Hash ও email credentials login form-এ দেবে না |
| Too many login attempts | ১৫ মিনিট অপেক্ষা করো; limiter bypass করতে multiple workers চালাবে না |
| HTML/blog preview unavailable | Session expired হলে নতুন করে sign in করো; লেখা copy করে রাখো |
| Data restart-এ হারাচ্ছে | Local SQLite নয়, Neon PostgreSQL configure করা আছে কি না দেখো |
| Build dependency mismatch | Repository-এর `requirements.txt` ব্যবহার করো; pins বদলালে tests চালাও |

## Official references

- [Render free limitations](https://render.com/docs/free)
- [Render Docker deployment](https://render.com/docs/docker)
- [Render environment variables](https://render.com/docs/configure-environment-variables)
- [Neon pricing](https://neon.com/pricing)
- [Neon connection guide](https://neon.com/docs/connect/connect-from-any-app)

Deployment সম্পন্ন এবং live যাচাই হয়েছে। Password, password hash ও database connection string private রাখবে; public chat বা GitHub-এ দেবে না।
