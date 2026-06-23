"""
SJS Job Scraper
===============
Scrapes job listings from Student Job Search (sjs.co.nz) and saves to CSV.

SETUP (run once):
    pip install playwright
    playwright install chromium

RUN:
    python scrape_sjs.py
"""

from playwright.sync_api import sync_playwright
import csv
from datetime import datetime
from urllib.parse import urlencode


def parse_date(date_str):
    """Convert 'Jun 23, 2026' to '2026-06-23' for proper date sorting."""
    if not date_str:
        return ""
    try:
        return datetime.strptime(date_str.strip(), "%b %d, %Y").strftime("%Y-%m-%d")
    except:
        return date_str  # return original if parsing fails

# ============================================================
#  CONFIG — edit these to change what you search for
# ============================================================

LOCATION  = "Otago, Dunedin, North Dunedin"  # Leave blank for all NZ
KEYWORDS  = ""                                 # e.g. "barista" or "admin"
WORK_TYPE = ""                                 # e.g. "Casual", "Permanent Part time",
                                               # "Fixed Term/Temporary", "Internship"
                                               # Leave blank for all types

OUTPUT_FILE = f"sjs_jobs_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"

# ============================================================
#  END CONFIG
# ============================================================


def build_url(location, keywords, work_type):
    params = {}
    if location:
        params["location"] = location
    if keywords:
        params["search"] = keywords
    if work_type:
        params["workType"] = work_type
    base = "https://www.sjs.co.nz/job-seeker/jobs"
    return f"{base}?{urlencode(params)}" if params else base


def get_text(el, selector):
    try:
        child = el.query_selector(selector)
        return child.inner_text().strip() if child else ""
    except:
        return ""


def scrape_current_page(pw_page):
    """Scrape job cards from whatever page is currently loaded."""
    cards = pw_page.query_selector_all(".JobCard_jobCard__qF84S")
    jobs = []

    for card in cards:
        try:
            job = {}

            # Title & URL
            link = card.query_selector(".JobCard_titleSection__ufhU7 h4 a")
            job["title"] = link.inner_text().strip() if link else ""
            href = link.get_attribute("href") if link else ""
            job["url"] = f"https://www.sjs.co.nz{href}" if href else ""

            # Company
            job["company"] = get_text(card, ".JobCard_company__AiuyK")

            # Location
            loc_el = card.query_selector(".JobCard_location__66eJV")
            job["location"] = loc_el.inner_text().strip() if loc_el else ""

            # Featured?
            job["featured"] = "Yes" if "JobCard_featured__rw9o_" in (card.get_attribute("class") or "") else "No"

            # Details columns
            detail_cols = card.query_selector_all(".JobCard_detailsColumn__FyrIs")

            if detail_cols:
                col1 = detail_cols[0]

                # Pay
                pay_el = col1.query_selector("strong")
                job["pay"] = pay_el.inner_text().strip() if pay_el else ""

                # Start date, hours, category from paragraphs
                job["start_date"] = ""
                job["hours_per_week"] = ""
                job["category"] = ""
                for p in col1.query_selector_all("p"):
                    text = p.inner_text().strip()
                    if "Start Date:" in text:
                        job["start_date"] = parse_date(text.replace("Start Date:", "").strip())
                    elif "Hours Per Week:" in text:
                        job["hours_per_week"] = text.replace("Hours Per Week:", "").strip()
                    elif text and "$" not in text and "Start Date" not in text and "Hours Per Week" not in text:
                        job["category"] = text
            else:
                job["pay"] = job["start_date"] = job["hours_per_week"] = job["category"] = ""

            # Description snippet (second column)
            if len(detail_cols) >= 2:
                desc_el = detail_cols[1].query_selector("p")
                job["description"] = desc_el.inner_text().strip() if desc_el else ""
            else:
                job["description"] = ""

            # Date posted
            job["date_posted"] = parse_date(get_text(card, ".JobCard_postedDate__1QZa3").replace("Created on:", "").strip())

            jobs.append(job)

        except Exception as e:
            print(f"  Warning: skipped a card ({e})")
            continue

    return jobs


def get_total_pages(pw_page):
    try:
        buttons = pw_page.query_selector_all(".Pagination_pageButton__GZPsV")
        return len(buttons) if buttons else 1
    except:
        return 1


def scrape_all(location, keywords, work_type):
    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pw_page = browser.new_page()

        url = build_url(location, keywords, work_type)
        print(f"\nSearching: {url}\n")

        pw_page.goto(url, wait_until="networkidle", timeout=30000)
        pw_page.wait_for_timeout(2000)

        # Check there are results
        if not pw_page.query_selector_all(".JobCard_jobCard__qF84S"):
            print("No job listings found.")
            browser.close()
            return all_jobs

        # Show total count
        count_el = pw_page.query_selector(".JobSearchPage_jobCountHeader__eNi1F span")
        total_pages = get_total_pages(pw_page)
        if count_el:
            print(f"{count_el.inner_text().strip()} across {total_pages} page(s)\n")

        # Scrape page 1
        jobs = scrape_current_page(pw_page)
        all_jobs.extend(jobs)
        print(f"Page 1: {len(jobs)} jobs scraped")

        # Click through remaining pages
        for pg in range(2, total_pages + 1):
            # Find and click the button for this page number
            buttons = pw_page.query_selector_all(".Pagination_pageButton__GZPsV")
            target = None
            for btn in buttons:
                if btn.inner_text().strip() == str(pg):
                    target = btn
                    break

            if not target:
                print(f"  Could not find page {pg} button, stopping.")
                break

            target.click()
            pw_page.wait_for_timeout(2500)  # wait for new jobs to load

            jobs = scrape_current_page(pw_page)
            all_jobs.extend(jobs)
            print(f"Page {pg}: {len(jobs)} jobs scraped")

        browser.close()

    return all_jobs


def save_to_csv(jobs, filename):
    if not jobs:
        print("No jobs to save.")
        return

    fields = ["title", "company", "location", "pay", "start_date",
              "hours_per_week", "category", "description",
              "date_posted", "featured", "url"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(jobs)

    print(f"\nSaved {len(jobs)} jobs to: {filename}")


def print_preview(jobs, max_preview=5):
    if not jobs:
        return
    print(f"\n{'='*60}")
    print(f"PREVIEW (first {min(max_preview, len(jobs))} of {len(jobs)} jobs)")
    print(f"{'='*60}")
    for job in jobs[:max_preview]:
        print(f"\nTitle      : {job['title']}")
        print(f"Company    : {job['company']}")
        print(f"Location   : {job['location']}")
        print(f"Pay        : {job['pay']}")
        print(f"Start Date : {job['start_date']}")
        print(f"Hrs/Week   : {job['hours_per_week']}")
        print(f"Category   : {job['category']}")
        print(f"Description: {job['description'][:80]}...")
        print(f"Posted     : {job['date_posted']}")
        print(f"URL        : {job['url']}")
    if len(jobs) > max_preview:
        print(f"\n... and {len(jobs) - max_preview} more in the CSV file.")


if __name__ == "__main__":
    print("SJS Job Scraper")
    print("---------------")
    print(f"Location : {LOCATION or 'All NZ'}")
    print(f"Keywords : {KEYWORDS or 'None'}")
    print(f"Work type: {WORK_TYPE or 'All types'}")

    jobs = scrape_all(LOCATION, KEYWORDS, WORK_TYPE)
    print_preview(jobs)
    save_to_csv(jobs, OUTPUT_FILE)
