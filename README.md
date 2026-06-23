# SJS Job Scraper

A Python script that scrapes job listings from [Student Job Search (sjs.co.nz)](https://www.sjs.co.nz) and exports them to CSV for filtering and analysis.

This is the script I used to find the job listing that led to building this portfolio.

---

## What it does

- Scrapes all job listings from SJS with optional filters for location, keywords, and work type
- Handles pagination automatically — scrapes every page of results
- Extracts title, company, location, pay, hours, start date, category, description, and URL for each listing
- Exports everything to a timestamped CSV for sorting and filtering in a spreadsheet
- Uses headless Chromium via Playwright so it renders JavaScript like a real browser

---

## Setup

```bash
pip install playwright
playwright install chromium
```

---

## Usage

Edit the config at the top of `scrape_sjs.py`:

```python
LOCATION  = "Otago, Dunedin, North Dunedin"  # Leave blank for all NZ
KEYWORDS  = ""                                 # e.g. "barista" or "admin"
WORK_TYPE = ""                                 # e.g. "Casual", "Permanent Part time"
```

Then run:

```bash
python scrape_sjs.py
```

Output is saved to a timestamped CSV: `sjs_jobs_YYYY-MM-DD_HH-MM.csv`

---

## Output columns

| Column | Description |
|--------|-------------|
| `title` | Job title |
| `company` | Employer name |
| `location` | Job location |
| `pay` | Pay rate |
| `start_date` | Start date (normalised to YYYY-MM-DD for sorting) |
| `hours_per_week` | Hours per week |
| `category` | Job category |
| `description` | Snippet from the listing |
| `date_posted` | Date posted (normalised to YYYY-MM-DD) |
| `featured` | Whether it's a featured listing |
| `url` | Direct link to the full listing |

---

## Tech stack

- Python 3
- [Playwright](https://playwright.dev/python/) — headless Chromium for JavaScript-rendered pages
- `csv` — standard library CSV export
- Built with AI assistance (Cursor)

---

## Why I built this

Manually browsing job listings page by page is slow. I wanted to pull everything into a spreadsheet, sort by pay and start date, and scan listings efficiently. Built and ran it the same day — found the listing for this role in the output CSV.

---

*Built in Dunedin, NZ 🇳🇿*
