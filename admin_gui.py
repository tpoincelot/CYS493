import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sqlite3
import os
# Our code
import course_scraper_html
import database

class ScraperAdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CCSU Course Scraper Admin")
        self.root.geometry("1200x600")
        
        # Make sure the database exists
        database.init_db()

        # Layout Configuration
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Control Panel
        control_frame = tk.Frame(self.root, pady=10, padx=10)
        control_frame.grid(row=0, column=0, sticky="ew")

        self.btn_run_scraper = tk.Button(control_frame, text="Run Scraper & Update DB", command=self.start_scraping_thread, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.btn_run_scraper.pack(side=tk.LEFT, padx=5)

        self.btn_clear_db = tk.Button(control_frame, text="Clear Stored Courses", command=self.clear_database, bg="#f44336", fg="white", font=("Arial", 10, "bold"))
        self.btn_clear_db.pack(side=tk.LEFT, padx=5)
        
        self.btn_refresh = tk.Button(control_frame, text="Refresh Table", command=self.load_data, font=("Arial", 10))
        self.btn_refresh.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = tk.Label(control_frame, textvariable=self.status_var, fg="blue")
        status_label.pack(side=tk.RIGHT, padx=10)

        # Data Table
        tree_frame = tk.Frame(self.root)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("ID", "Code", "Title", "URL")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor=tk.W)
        self.tree.column("ID", width=50, stretch=tk.NO)
        self.tree.column("URL", width=300)

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Initial Load
        self.load_data()

    def load_data(self):
        # Clear current data
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        try:
            conn = sqlite3.connect(database.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, code, title, url FROM courses")
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                self.tree.insert("", tk.END, values=row)
            self.status_var.set(f"Loaded {len(rows)} courses from database.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not load data:\n{e}")

    def clear_database(self):
        confirm = messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all stored courses from the database? This cannot be undone.")
        if confirm:
            try:
                conn = sqlite3.connect(database.DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM courses")
                conn.commit()
                conn.close()
                self.load_data()
                self.status_var.set("Database cleared successfully.")
                messagebox.showinfo("Success", "All courses have been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear database:\n{e}")

    def start_scraping_thread(self):
        # Disable buttons while scraping
        self.btn_run_scraper.config(state=tk.DISABLED)
        self.btn_clear_db.config(state=tk.DISABLED)
        self.status_var.set("Scraping in progress... Please wait.")
        
        # Run scraper in a background thread so the GUI doesn't freeze
        thread = threading.Thread(target=self.run_scraper)
        thread.start()

    def run_scraper(self):
        try:
            # The scrape function in course_scraper_html already writes to the DB via save_courses
            courses = course_scraper_html.scrape("ccsu_courses_html.json")
            
            # Update the GUI safely from the thread
            self.root.after(0, self.scraping_complete, len(courses))
        except Exception as e:
            self.root.after(0, self.scraping_failed, str(e))

    def scraping_complete(self, num_courses):
        self.btn_run_scraper.config(state=tk.NORMAL)
        self.btn_clear_db.config(state=tk.NORMAL)
        self.load_data()
        self.status_var.set(f"Scraping complete! {num_courses} courses processed.")
        messagebox.showinfo("Success", f"Scraper finished successfully.\nProcessed {num_courses} courses.")

    def scraping_failed(self, error_msg):
        self.btn_run_scraper.config(state=tk.NORMAL)
        self.btn_clear_db.config(state=tk.NORMAL)
        self.status_var.set("Scraping failed.")
        messagebox.showerror("Scraper Error", f"An error occurred while scraping:\n{error_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperAdminGUI(root)
    root.mainloop()
