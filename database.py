import sqlite3

# name of the database file that will be created locally
DB_NAME = "courses.db"

# create the database and table if it doesnt already exist
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # creating courses table to store scraped data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        title TEXT,
        description TEXT,
        url TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()


# take list of courses from crawler and insert into database
def save_courses(courses):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # loop through each course and insert it
    for course in courses:
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO courses (code, title, description, url)
            VALUES (?, ?, ?, ?)
            """, (
                course["code"],
                course["title"],
                course["description"],
                course["url"]
            ))
        except Exception as e:
            print("error inserting:", e)

    conn.commit()
    conn.close()