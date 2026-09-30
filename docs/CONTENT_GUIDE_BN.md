# Portfolio update ও blog লেখার নিয়ম

## Admin studio

`/admin/login` থেকে sign in করলে `/admin`-এ Content studio খোলে। Profile, projects, publications, blog posts, experience ও grants/credentials আলাদা list-এ পাওয়া যাবে। প্রতিটি record **Add**, **Edit** ও **Delete** করা যায়।

## Profile, links ও skills

**Edit profile & links**-এ নাম, role, headline, summary, about, email, availability, education status এবং GitHub/Scholar/ORCID/LinkedIn update করা যায়। Links full `https://...` হবে।

Skills এক group per line:

```text
AI & ML: PyTorch, scikit-learn, OpenCV
Backend & deployment: FastAPI, Docker, Git
Databases: PostgreSQL, MySQL, SQL Server
```

Result হলে education status বদলাও। Pending result-এর কারণে initial portfolio-তে final CGPA দেখানো হয়নি। Website CV এই একই updated content পড়ে।

## Project case study

প্রতিটি project-এ রাখো:

1. **Title:** ছোট, নির্দিষ্ট নাম।
2. **Category:** Research বা Engineering।
3. **Role:** তুমি কী করেছ; দলগত কাজ হলে সেটি স্পষ্ট করো।
4. **Summary:** visitor-এর জন্য ১–২ sentence।
5. **Problem:** কার কী সমস্যা ছিল।
6. **Approach:** design, data বা implementation-এর মূল সিদ্ধান্ত।
7. **Outcome:** সত্যিকারের ফল ও প্রযোজ্য সীমাবদ্ধতা।
8. **Tags:** comma-separated technologies/topics।
9. **GitHub / Demo:** actual verified link; demo না থাকলে খালি রাখো।
10. **Featured:** home page-এর selected work-এ দেখাবে কি না।

**Display order** ছোট হলে আগে আসে। **Make this entry visible** unchecked থাকলে private draft। Featured checkbox alone কোনো draft public করে না।

## Publication status বনাম visibility

| Setting | অর্থ |
| --- | --- |
| Published | আসল publication প্রকাশিত |
| Submitted | manuscript জমা দেওয়া হয়েছে; প্রকাশিত নয় |
| In preparation | লেখা/সংশোধন চলছে বা submission planned |
| First author | ওই paper-এ তোমার first-author role |
| Make visible | portfolio-তে entry দেখাবে কি না |

Published paper count শুধু visible `Published` entries থেকে হিসাব হয়। Submitted/first-author manuscripts published count বাড়ায় না। Status change করার সময় সত্যিকারের progress অনুযায়ী update করো। DOI field-এ identifier দাও, যেমন `10.1109/PECCII70991.2026.11661902`; DOI URL নয়।

## Blog লেখা

1. **Blog posts → Add post**।
2. Title, summary, date, tags ও body লেখো।
3. URL slug English lowercase দাও, যেমন `fastapi-ml-serving`। English title হলে suggested slug হয়; Bengali title হলে নিজের English slug দাও।
4. **Preview writing**-এ Markdown rendering দেখো।
5. Visibility unchecked রেখে **Save changes** → private draft।
6. Publish করতে আবার edit করে **Make this entry visible** check ও save।

Draft public URL, blog list, sitemap ও RSS-এ পাওয়া যায় না। Included sample article-টি private outline; নিজের লেখা দিয়ে edit করার পরে publish করবে। এই release-এ scheduled publishing নেই; date metadata, visibility checkbox publishing নিয়ন্ত্রণ করে।

### Markdown example

````markdown
# আমার প্রথম research note

আজ লিখছি **FastAPI** দিয়ে model serving নিয়ে।

## কী শিখলাম

- Input validation দরকার।
- Preprocessing consistent হতে হবে।
- Evaluation protocol পরিষ্কার করা দরকার।

[Source code](https://github.com/roton43/inference-api-with-fastapi)

```python
from fastapi import FastAPI
app = FastAPI()
```

| Decision | Reason |
| --- | --- |
| FastAPI | Validated inference interface |
````

Headings, emphasis, lists, HTTPS links, tables ও code blocks আছে। এই version-এ article image uploads নেই; raw HTML sanitized হয়।

## Backup ও restore

**Download content backup** সব content-এর JSON দেয়, including drafts। Restore current content replace করে, তাই আগে current backup রাখো। `seed.json` শুধু প্রথম database initialization-এর জন্য। চলমান site-এর content change করতে editor ব্যবহার করো।

## Design change কোথায়

| কাজ | File |
| --- | --- |
| Colors, spacing, typography | `app/static/style.css`-এর `:root` variables ও styles |
| Home sections | `app/templates/home.html` |
| Project detail layout | `app/templates/project.html` |
| Public navigation/footer | `app/templates/base.html` |
| Blog rendering | `app/templates/post.html` ও server sanitizer |
| নতুন content field | `app/schemas.py`, relevant template ও migration পরিকল্পনা |

Design/code change-এর পরে test করে GitHub-এ push ও redeploy করবে। Content edits-এর জন্য redeploy দরকার নেই।
