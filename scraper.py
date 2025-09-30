# scraper.py (Final Version: Cloudscraper)
import os
from datetime import datetime
import cloudscraper # Use cloudscraper instead of requests
from bs4 import BeautifulSoup
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
    """Scrapes Social Blade using cloudscraper to bypass bot detection."""
    print("Starting scraper (Cloudscraper method)...")
    
    # Create a scraper instance that can bypass Cloudflare
    scraper = cloudscraper.create_scraper()
    
    try:
        # Use the scraper instance just like you would use 'requests'
        response = scraper.get(SOCIALBLADE_URL)
        if response.status_code != 200:
            print(f"Error: Failed to fetch page. Status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the 'FOLLOWING' label, then find the next sibling span which holds the number
        following_label = soup.find('span', string='FOLLOWING')
        if not following_label:
            print("Error: Could not find the 'FOLLOWING' label.")
            return

        following_value_element = following_label.find_next_sibling('span')
        if not following_value_element:
            print("Error: Could not find the following count value element.")
            return
        
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
        print("Scraper finished.")

if __name__ == '__main__':
    setup_database()
    scrape_and_save_count()