import json
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import concurrent.futures
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
import time
import threading
import logging

# Configure logging for auditing and error-handling
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
    handlers=[
        logging.FileHandler("crawler_audit.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

BASE_URL = "https://ccsu.smartcatalogiq.com"
USER_AGENT = "CourseScraperBot/1.0"
HEADERS = {'User-Agent': USER_AGENT}

# Configure automatic retries for recoverable errors
http_session = requests.Session()
retry_strategy = Retry(
    total=5,  # Maximum number of retries
    backoff_factor=1,  # Time between retries factor
    status_forcelist=[408, 429, 500, 502, 503, 504],  # HTTP status codes
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http_session.mount("https://", adapter)
http_session.mount("http://", adapter)

# Read robots.txt
rp = RobotFileParser()
rp.set_url(urljoin(BASE_URL, "/robots.txt"))
try:
    rp.read()
    logging.info("Successfully read robots.txt")
except Exception as e:
    logging.warning(f"Could not read robots.txt: {e}")

# Get crawl delay from robots.txt or default to 0.1
CRAWL_DELAY = rp.crawl_delay(USER_AGENT) or 0.1
logging.info(f"Using crawl delay of {CRAWL_DELAY} seconds")
last_request_time = 0.0
request_lock = threading.Lock()

def polite_request(url, timeout=15):
    """Makes an HTTP GET request respecting the crawl delay across all threads."""
    global last_request_time
    with request_lock:
        elapsed = time.time() - last_request_time
        if elapsed < CRAWL_DELAY:
            time.sleep(CRAWL_DELAY - elapsed)
        # Update last_request_time before releasing lock
        last_request_time = time.time()
        
    # Perform network request outside the lock so other threads aren't blocked from waiting
    logging.debug(f"Fetching URL: {url}")
    return http_session.get(url, headers=HEADERS, timeout=timeout)

def get_latest_catalog_url():
    """Find the URL for the current/latest catalog year."""
    if not rp.can_fetch(USER_AGENT, BASE_URL):
        logging.warning(f"Access to {BASE_URL} denied by robots.txt")
        return BASE_URL + "/en/2024-2025/undergraduate-graduate-catalog"

    try:
        resp = polite_request(BASE_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Look for the first catalog link in the archived catalogs list
        for a in soup.find_all('a'):
            href = a.get('href') or ''
            if re.search(r'/en/\d{4}-\d{4}/[a-z-]+-catalog$', href, re.IGNORECASE):
                logging.info(f"Found latest catalog URL: {BASE_URL + href}")
                return BASE_URL + href
    except Exception as e:
        logging.error(f"Error fetching base catalog URL: {e}", exc_info=True)
        
    # Fallback default
    logging.info("Using fallback default catalog URL")
    return BASE_URL + "/en/2024-2025/undergraduate-graduate-catalog"

def fetch_subject_courses(subj_url):
    """Fetch all courses listed on a specific subject page."""
    courses = []
    if not rp.can_fetch(USER_AGENT, subj_url):
        logging.warning(f"Access to {subj_url} denied by robots.txt")
        return courses

    try:
        resp = polite_request(subj_url, timeout=15)
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
        logging.info(f"Successfully scraped {len(courses)} courses from {subj_url}")
    except Exception as e:
        logging.error(f"Error fetching {subj_url}: {e}", exc_info=True)
        
    return courses

def parse_courses_html():
    catalog_url = get_latest_catalog_url()
    courses_url = catalog_url + "/all-courses"
    logging.info(f"Fetching catalog from: {courses_url}")
    
    if not rp.can_fetch(USER_AGENT, courses_url):
        logging.warning(f"Access to {courses_url} denied by robots.txt")
        return []
    
    try:
        resp = polite_request(courses_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching all courses page {courses_url}: {e}", exc_info=True)
        return []

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
    logging.info(f"Found {len(subject_links)} subjects. Fetching course links...")

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
    logging.info("Scraping courses from HTML...")
    parsed = parse_courses_html()

    # added by weronika import database functions
    from database import init_db, save_courses

    # added by weronika initialize db and save scraped data
    init_db()
    save_courses(parsed)

    
    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
            
    return parsed

if __name__ == "__main__":
    try:
        courses = scrape("ccsu_courses_html.json")
        logging.info(f"Scraped {len(courses)} courses and wrote ccsu_courses_html.json")
    except Exception as e:
        logging.error("Critical error scraping courses:", exc_info=True)
