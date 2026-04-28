# CCSU Course Scraper

A Python-based web crawler designed to retrieve and index course data from the Central Connecticut State University (CCSU) SmartCatalog. This crawler is built with a focus on **ethical web scraping guidelines**, ensuring it respects target server rules.

## Features

* **Robots.txt Compliance**: Automatically parses and respects the site's `robots.txt` rules before fetching any URLs.
* **Polite Rate Limiting**: Implements a thread-safe rate limiter that respects the `Crawl-delay` directive (or defaults to a set delay) to avoid overloading the server.
* **Automatic Retries & Exponential Backoff**: Gracefully handles network instability and recoverable server-side HTTP errors (e.g., 429, 500, 502, 503, 504) by pausing and retrying failed requests up to 5 times.
* **Audit Logging**: Detailed logging of all crawler activities, threads, and errors to a local `crawler_audit.log` file for observability and troubleshooting.
* **Concurrent Execution**: Utilizes multi-threading to speed up the scraping process safely and responsibly, without violating the global rate limits.
* **SQLite Database**: Automatically saves scraped course information to a local SQLite database (`courses.db`) using the integrated `database.py` script.
* **Admin GUI**: A built-in graphical user interface (`admin_gui.py`) constructed with `tkinter` allows you to manage the database, trigger the scraper, and clear stored data without typing terminal commands.

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed on your system. If you are on Linux and plan to use the Admin GUI, you may need to install the system-level Tkinter library:
```bash
sudo apt-get install python3-tk -y
```

### 2. Environment Setup
It is highly recommended to run this project inside a Python virtual environment to keep dependencies isolated.

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

### Using the Admin GUI (Recommended)
The easiest way to operate the scraper and view the data is via the built-in graphical interface:

```bash
python3 admin_gui.py
```
From the GUI window, you can view the data table, click **Run Scraper & Update DB** to execute a scrape job, and click **Clear Stored Courses** to easily clear the database table.

### Using the CLI
To run the HTML crawler script directly from the terminal:

```bash
python3 course_scraper_html.py
```

### Outputs
Once the run is complete, the project produces three primary files:
1. **`courses.db`**: An SQLite database containing the `courses` table which persistently stores all scraped entries.
2. **`ccsu_courses_html.json`**: A JSON dump containing an array of the scraped courses. Each entry includes the course code, title, description, and source URL.
3. **`crawler_audit.log`**: A log file capturing the crawler's progress, active threads, rate-limit compliance, and full tracebacks of any errors encountered during the run.