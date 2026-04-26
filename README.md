# CCSU Course Scraper

A Python-based web crawler designed to retrieve and index course data from the Central Connecticut State University (CCSU) SmartCatalog. This crawler is built with a focus on **ethical web scraping guidelines**, ensuring it respects target server rules.

## Features

* **Robots.txt Compliance**: Automatically parses and respects the site's `robots.txt` rules before fetching any URLs.
* **Polite Rate Limiting**: Implements a thread-safe rate limiter that respects the `Crawl-delay` directive (or defaults to a set delay) to avoid overloading the server.
* **Automatic Retries & Exponential Backoff**: Gracefully handles network instability and recoverable server-side HTTP errors by pausing and retrying failed requests up to 5 times.
* **Audit Logging**: Detailed logging of all crawler activities, threads, and errors to a local `crawler_audit.log` file for troubleshooting.
* **Concurrent Execution**: Utilizes multi-threading to speed up the scraping process safely and responsibly, without violating the global rate limits.

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed on your system.

### 2. Environment Setup
Run this project inside a Python virtual environment to keep dependencies isolated.

```bash
# Navigate to the project directory
cd CYS493_project

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
Install the required third-party Python packages (`requests`, `beautifulsoup4`, etc.).

```bash
pip install -r requirements.txt
```

## Usage

To start the HTML crawler, ensure your virtual environment is active and run the main script:

```bash
python3 course_scraper_html.py
```

### Outputs
Once the run is complete, the script produces two primary files:
1. **`ccsu_courses_html.json`**: A JSON file containing an array of the scraped courses. Each entry includes the course code, title, description, and source URL.
2. **`crawler_audit.log`**: A log file capturing the crawler's progress, active threads, rate-limit compliance, and full tracebacks of any errors encountered during the run.

## Deployment

If you plan to deploy this scraper for periodic updates in a production environment:

1. **Server Environment**: The script is fully headless and runs perfectly on standard Linux servers.
2. **Periodic Automation (Cron Jobs)**: You can set up a cron job to keep your catalog index up to date automatically.
3. **Log Management**: For long-term deployments, configure a tool like `logrotate` for `crawler_audit.log` to prevent the log file from consuming a large amount of storage space over time.