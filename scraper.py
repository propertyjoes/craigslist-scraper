import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2 import service_account
import gspread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Sheets Setup
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_SHEETS_CREDENTIALS')

def get_google_sheet():
    """Authenticate and return the Google Sheet"""
    creds = service_account.Credentials.from_service_account_info(
        eval(SERVICE_ACCOUNT_INFO), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def scrape_craigslist_email(url):
    """Scrape email from Craigslist listing"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    try:
        # Click reply button
        reply_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[@class="reply-button js-only"]'))
        reply_button.click()
        
        # Wait for dropdown
        time.sleep(2)
        
        # Click email option
        email_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[@class="reply-option-header"]')))
        email_option.click()
        
        # Extract email
        email_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="reply-email-address"]')))
        return email_element.text.strip()
    
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None
    finally:
        driver.quit()

def process_sheet():
    """Main function to process all rows in sheet"""
    sheet = get_google_sheet()
    records = sheet.get_all_records()
    
    for i, row in enumerate(records, start=2):  # start=2 because sheets are 1-indexed and header is row 1
        url = row.get('URL')  # Assuming column A header is "URL"
        
        # Skip if no URL or email already exists
        if not url or sheet.cell(i, 2).value:  # Column B is index 2
            continue
            
        print(f"Processing {url}")
        email = scrape_craigslist_email(url)
        
        if email:
            print(f"Found email: {email}")
            sheet.update_cell(i, 2, email)  # Update Column B
            time.sleep(2)  # Be polite to Craigslist
        else:
            sheet.update_cell(i, 2, "NOT FOUND")

if __name__ == "__main__":
    process_sheet()