# প্রথম থেকে চালানোর নির্দেশনা

তোমার জন্য বানানো project-এ FastAPI website, admin editor, research publications, industry project case studies, blog, Docker ও deployment configuration সব রয়েছে। Website-এর public content English রাখা হয়েছে, যাতে international academic ও industry visitors পড়তে পারেন। Blog-এ বাংলা ও English দুটোই লেখা যাবে।

## ১. ZIP extract করো

`Roton_Portfolio_Project.zip` extract করলে `roton-portfolio` folder পাবে। Terminal-এ সেই folder-এ ঢুকো। পরের সব command এই folder থেকে চালাবে।

## ২. Python environment তৈরি করো

Python 3.12 ব্যবহার করো। Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

PowerShell activation blocked হলে activation ছাড়াই `.venv\Scripts\python.exe` দিয়ে commands চালাতে পারো।

## ৩. Admin password তৈরি করো

```bash
python -m scripts.password
```

কমপক্ষে ১৪-character password দাও এবং confirm করো। টাইপ করার সময় password দেখা যাবে না। Output-এ `ADMIN_PASSWORD_HASH=...` আসবে। এটি `.env`-এ ওই field-এর value হিসেবে বসাও। Hash-এ `$` থাকে, তাই `.env`-এ single quote ব্যবহার করো:

```dotenv
ADMIN_PASSWORD_HASH='pbkdf2_sha256$...'
```

এই উদাহরণের `...` copy করবে না—তোমার নিজের সম্পূর্ণ generated hash বসাবে। Password plaintext `.env`-এ রাখবে না। Default username `roton`; চাইলে বদলাতে পারো।

## ৪. Session secret তৈরি করো

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Output-টি `.env`-এর `SESSION_SECRET`-এ বসাও। Local setup:

```dotenv
APP_ENV=development
SITE_URL=http://localhost:8000
ALLOWED_HOSTS=localhost,127.0.0.1
SESSION_SECRET=your-generated-secret
ADMIN_USERNAME=roton
ADMIN_PASSWORD_HASH='your-generated-complete-hash'
DATABASE_URL=
```

`your-generated-...` অংশগুলো নিজের actual value দিয়ে বদলাবে। Local run-এ `DATABASE_URL` খালি থাকলে SQLite file তৈরি হয়। Admin password hash খালি রাখলে public site চলবে, কিন্তু admin login disabled থাকবে।

## ৫. Website চালাও

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Website: `http://localhost:8000`
- Admin login: `http://localhost:8000/admin/login`
- Health endpoint: `http://localhost:8000/health`
- Printable CV: `http://localhost:8000/cv`

Server বন্ধ করতে terminal-এ Ctrl+C। পরে চালাতে environment activate করে একই Uvicorn command দাও। প্রথম boot-এ তোমার initial content database-এ ঢুকবে; পরের boot-এ editor-এর changes থাকবে।

## ৬. Docker দিয়ে চালাও

Docker Engine এবং Compose plugin, অথবা Docker Desktop install করা থাকতে হবে। `.env` তৈরি করে password/secret বসানোর পর:

```bash
docker compose up --build -d
docker compose logs -f web
```

Docker Compose নিজে PostgreSQL চালু করে। Browser-এ `http://localhost:8000` খোলো। Database port বাইরে expose করা হয়নি। Data `portfolio_postgres` volume-এ থাকে।

```bash
docker compose down
docker compose up -d
```

এই stop/start-এ data থাকে। `docker compose down -v` দিলে database volume মুছে যাবে—নিয়মিত বন্ধ করার জন্য `-v` ব্যবহার করবে না। প্রথমে `/admin` থেকে content backup download করে রাখতে পারো।

## ৭. প্রথমবার content review

Admin studio-তে গিয়ে:

1. Profile, contact email, availability ও social links দেখো।
2. Result প্রকাশ হলে education status update করো; final CGPA নিশ্চিত হলে status বা about text-এ যোগ করতে পারো।
3. Journal submit হলে সংশ্লিষ্ট publication status `Submitted` করো।
4. NetroLekha data article-এর exact submitted title ও author list বসাও।
5. Project demo URL থাকলে verified current URL যোগ করো।
6. Sample blog private draft edit করে নিজের প্রথম article লিখো।

পরের ধাপ: [Free deployment guide](DEPLOYMENT_BN.md)।
