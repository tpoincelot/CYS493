import json
import re
import requests

# The JSON endpoint
COURSES_JSON_URL = "https://ccsu.smartcatalogiq.com/Institutions/Central-Connecticut-State-University/json/Current/courses-E0BE071D-F43A-4699-B2E8-55BAC81A7857.json"

def fetch_courses_json(url=COURSES_JSON_URL, timeout=20):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def parse_courses(json_data):
    courses = []
    
    for course in json_data:
        number = course.get("number", "").strip()
        title = course.get("name", "").strip()
        url_path = course.get("url", "")
        url = f"https://ccsu.smartcatalogiq.com{url_path}" if url_path else ""
        
        # Validity check
        if not (number or title):
            continue

        code = number
        if url_path:
            m = re.search(r"/([^/]+)-(\d+[A-Za-z]*)$", url_path)
            if m:
                code = f"{m.group(1)} {m.group(2)}".upper()
            
        courses.append({
            "code": code,
            "title": title,
            "description": "",
            "url": url
        })

    return courses

def scrape(output_json=None):
    print("Fetching course data directly from JSON API...")
    raw_json = fetch_courses_json()
    
    if isinstance(raw_json, dict):
        raw_json = raw_json.get("Courses") or list(raw_json.values())[0]
            
    parsed = parse_courses(raw_json)
    
    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
    return parsed

if __name__ == "__main__":
    try:
        courses = scrape("ccsu_courses.json")
        print(f"Scraped {len(courses)} courses and wrote ccsu_courses.json")
    except Exception as e:
        print("Error scraping courses:", e)
