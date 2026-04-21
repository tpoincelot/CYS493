import json
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

BASE_URL = "https://ccsu.smartcatalogiq.com"
USER_AGENT = "CourseScraperBot/1.0"
HEADERS = {'User-Agent': USER_AGENT}

# Initialize and read robots.txt
rp = RobotFileParser()
rp.set_url(urljoin(BASE_URL, "/robots.txt"))
try:
    rp.read()
except Exception as e:
    print(f"Warning: Could not read robots.txt: {e}")

def get_latest_catalog_url():
    """Find the URL for the current/latest catalog year."""
    if not rp.can_fetch(USER_AGENT, BASE_URL):
        print(f"Access to {BASE_URL} denied by robots.txt")
        return BASE_URL + "/en/2024-2025/undergraduate-graduate-catalog"

    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for the first catalog link in the archived catalogs list
        for a in soup.find_all('a'):
            href = a.get('href') or ''
            if re.search(r'/en/\d{4}-\d{4}/[a-z-]+-catalog$', href, re.IGNORECASE):
                return BASE_URL + href
    except Exception as e:
        print(f"Error fetching base catalog URL: {e}")
        
    # Fallback default if extraction fails
    return BASE_URL + "/en/2024-2025/undergraduate-graduate-catalog"

def fetch_subject_courses(subj_url):
    """Fetch all courses listed on a specific subject page."""
    courses = []
    if not rp.can_fetch(USER_AGENT, subj_url):
        print(f"Access to {subj_url} denied by robots.txt")
        return courses

    try:
        resp = requests.get(subj_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # The path part of the subject URL
        subj_path = subj_url.replace(BASE_URL, "")
        
        for a in soup.find_all('a'):
            href = a.get('href') or ''
            
            # Course links have exactly 2 more slash segments than the subject page link
            if href.startswith(subj_path + "/") and href.count('/') == subj_path.count('/') + 2:
                text = a.text.strip()
                if not text:
                    continue
                
                # Separate the code (like "AAPI 110") from the title
                m_text = re.match(r'^([A-Za-z-]+\s+\d+[A-Za-z]*)\s+(.*)$', text)
                if m_text:
                    code = m_text.group(1).upper()
                    title = m_text.group(2).strip()
                else:
                    # Fallback URL parsing
                    m_url = re.search(r"/([^/]+)-(\d+[A-Za-z]*)$", href)
                    if m_url:
                        code = f"{m_url.group(1)} {m_url.group(2)}".upper()
                    else:
                        code = text.split(' ')[0] if ' ' in text else "UNKNOWN"
                    
                    title = text
                    if title.upper().startswith(code.upper()):
                        title = title[len(code):].strip()

                courses.append({
                    "code": code,
                    "title": title,
                    "description": "",
                    "url": BASE_URL + href
                })
    except Exception as e:
        print(f"Error fetching {subj_url}: {e}")
        
    return courses

def parse_courses_html():
    catalog_url = get_latest_catalog_url()
    courses_url = catalog_url + "/all-courses"
    print(f"Fetching catalog from: {courses_url}")
    
    if not rp.can_fetch(USER_AGENT, courses_url):
        print(f"Access to {courses_url} denied by robots.txt")
        return []
    
    resp = requests.get(courses_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    courses_path = courses_url.replace(BASE_URL, "")
    subject_links = set()
    
    # Find all subject links
    for a in soup.find_all('a'):
        href = a.get('href') or ''
        # Subject links have exactly 1 more slash segment than the all-courses link
        if href.startswith(courses_path + "/") and href.count('/') == courses_path.count('/') + 1:
            subject_links.add(BASE_URL + href)
            
    subject_links = list(subject_links)
    print(f"Found {len(subject_links)} subjects. Fetching course links...")

    all_courses = []
    
    # for concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_subject_courses, url): url for url in subject_links}
        for future in concurrent.futures.as_completed(future_to_url):
            subj_courses = future.result()
            all_courses.extend(subj_courses)
            
    # Deduplicate based on URL
    unique_courses = {c['url']: c for c in all_courses}.values()
    return list(unique_courses)

def scrape(output_json=None):
    print("Scraping courses from HTML...")
    parsed = parse_courses_html()
    
    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
            
    return parsed

if __name__ == "__main__":
    try:
        courses = scrape("ccsu_courses_html.json")
        print(f"Scraped {len(courses)} courses and wrote ccsu_courses_html.json")
    except Exception as e:
        print("Error scraping courses:", e)
