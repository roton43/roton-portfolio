# Content provenance and confirmation notes

Verified / assembled on 30 September 2026. This is an internal maintainer note, not a public website page.

## Authoritative input

- Attached `AI_ML CV.pdf` and `Research_CV.pdf`: identity, contact email, experience, education period, grants, skills, project descriptions and selected publications.
- User's latest instruction: degree work completed, result not released; expected in the first week of October. Portfolio uses a dated pending-status statement rather than predicting an official release date.
- User confirmed total **nine published conference papers: eight coauthored, plus one first-authored**.
- User's latest manuscript update: one Data in Brief submission and two first-author journal manuscripts planned for submission. Older CV wording such as “under review” for those journal manuscripts is superseded.
- User explicitly reported SQL Server, MySQL, PostgreSQL, FastAPI, Docker, HTML and CSS knowledge.

## Profile links extracted from actual PDF hyperlinks

- GitHub: https://github.com/roton43
- Google Scholar: https://scholar.google.com/citations?user=jxq8PjQAAAAJ
- ORCID: https://orcid.org/0009-0003-6466-7402
- LinkedIn: https://linkedin.com/in/md-roton-ahmed-6bb396216

Google Scholar's public listing was retrieved and matched to nine conference works. Public ORCID work metadata was retrieved from the ORCID API. Duplicate ORCID work entries were deduplicated by DOI; two additional ORCID items outside the user's confirmed nine-paper list were not silently included in the nine-paper count. LinkedIn automated page retrieval was blocked, so no additional job claims were inferred from it. No citation count or h-index is presented.

## Publication records

Titles and author lists were checked against Crossref DOI metadata wherever available. The road-accident DOI request returned a rate limit; its title/authors come from the supplied Research CV and matching Google Scholar/ORCID entries. Conference dates are shown consistently with the conference venue; Springer online release dates can differ from the proceedings/conference year.

| Work | DOI | First author |
| --- | --- | --- |
| Cross-lingual font recognition | 10.1109/PECCII70991.2026.11661902 | Yes |
| Automated plant irrigation robot | 10.1109/QPAIN66474.2025.11171837 | No |
| Genetic syndrome classification | 10.1109/RAAICON69033.2025.11502155 | No |
| Bangladeshi dialect classification | 10.1007/978-3-032-11352-8_1 | No |
| Road accident determinants | 10.1007/978-3-032-11355-9_33 | No |
| Bangla BERT register classification | 10.1109/ICCIT68739.2025.11490255 | No |
| Bone fracture detection / XAI | 10.1109/COMPAS67506.2025.11381823 | No |
| EEG depression detection | 10.1007/978-3-032-11335-1_18 | No |
| Handwriting-based ADHD detection | 10.1109/QPAIN66474.2025.11171830 | No |

## Repository evidence

The public GitHub repository inventory was retrieved from the GitHub API. READMEs were inspected for:

- `Handwriting-Data-Collector`
- `brain-tumor-classifier`
- `inference-api-with-fastapi`
- `mall-customer-segmentation`
- `stock-price-forecasting`
- `fake-news-classifier`

`House_Price_Prediction` is supported by the CV and repository description. `GazeTypeBD` has no README; its public repository existence/structure was checked and the case study is grounded in the CV. Irrigation work is linked through its DOI on the research page; no repository URL was invented.

The segmentation case study describes the verified Streamlit implementation. It does not assume that a separate FastAPI/Railway version mentioned in the CV is currently live. Historical stock-dashboard demo links were not represented as current live demos without endpoint verification. Demo fields are ready for the owner to add current verified URLs.

No repository accuracy figures are promoted as independently verified benchmarks. NetroLekha study figures are explicitly described as CV-reported; the underlying unpublished corpus was not reanalyzed for this task. Medical and text-classification case studies are described as prototypes with the limits relevant to interpreting those results.

## Owner confirmation still useful

1. Exact submitted Data in Brief title and complete final author list. The initial entry is a descriptive corpus title with the owner's first-author role, not a fabricated full journal citation.
2. Final journal target venues and author lists before submission. The thesis author list preserves the CV's abbreviated names; the NetroLekha system CV lists the owner as sole author.
3. Final official result and CGPA after release. CV-listed 3.51 is omitted from the public portfolio while the result is pending.
4. Current project demos or research dataset DOI to add, if available. No Mendeley dataset DOI was invented.
5. A profile photograph, if desired. Initial version deliberately uses typographic branding and does not invent a portrait.

These items can be updated using the content studio; they do not prevent local use or deployment.

## Privacy choices

Public contact email and owner-provided professional profile links are included. Telephone numbers, referee email addresses, original CV PDFs, raw participant records and unpublished data are not bundled as public assets. Printable CV is generated from current curated website content.

## Bundled font

Noto Sans Bengali (Google Fonts / Noto project), regular, medium, semibold and bold, is self-hosted under `app/static/fonts/`. The SIL Open Font License is included as `OFL.txt`. Font files came from the official Google Fonts stylesheet and font CDN; no external font requests are needed by visitors.
