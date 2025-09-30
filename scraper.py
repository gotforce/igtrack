# scraper.py
import os
import sqlite3 # Keep for local testing if needed, but not used in production
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, text, inspect

# --- Configuration ---
TARGET_ACCOUNT = 'thebeardyengineer'
SOCIALBLADE_URL = f'https://socialblade.com/instagram/user/{TARGET_ACCOUNT}'

# Get the database URL from Render's environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for scraper")

engine = create_engine(DATABASE_URL)

def setup_database():
    """Connects to the database and creates the table if it doesn't exist."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        if not inspector.has_table('following_history'):
            print("Creating 'following_history' table...")
            conn.execute(text('''
                CREATE TABLE following_history (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    following_count INTEGER NOT NULL
                )
            '''))
            conn.commit()
            print("Table created.")
        else:
            print("Table 'following_history' already exists.")

def scrape_and_save_count():
    """Scrapes Social Blade using a resource-optimized Selenium browser."""
    print("Starting scraper (Social Blade Selenium method - Lean Mode)...")
    
    # --- UPDATED OPTIONS ---
    # These options are optimized for running in a constrained cloud environment
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--single-process") # Crucial for reducing memory usage
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Disable image loading to save memory
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    # --- END OF UPDATED OPTIONS ---

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        print(f"Navigating to {TARGET_ACCOUNT}'s profile on Social Blade...")
        driver.get(SOCIALBLADE_URL)
        
        print("Finding following count...")
        following_value_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[text()='FOLLOWING']/following-sibling::span")
        ))
        
        following_count_str = following_value_element.text.strip().replace(',', '')
        following_count = int(following_count_str)
        print(f"Successfully found following count: {following_count}")

        # Save to PostgreSQL Database
        with engine.connect() as conn:
            timestamp = datetime.now()
            stmt = text("INSERT INTO following_history (timestamp, following_count) VALUES (:ts, :count)")
            conn.execute(stmt, {"ts": timestamp, "count": following_count})
            conn.commit()
            print("Data saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        print("Scraper finished.")

if __name__ == '__main__':
    setup_database()
    scrape_and_save_count()