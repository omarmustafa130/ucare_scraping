from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import gspread
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser
import pandas as pd
import time
import random

# Google Sheets setup
# OAuth2 client secrets file
CLIENT_SECRET_FILE = 'CLIENT-SECRET.json'
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
storage = Storage('credentials.json')  # Save the credentials token here
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=SCOPE)
credentials = storage.get()

if not credentials or credentials.invalid:
    flags = argparser.parse_args(args=[])
    credentials = run_flow(flow, storage, flags)

gc = gspread.authorize(credentials)
sheet = gc.open("Omar").sheet1  # Replace "Omar" with your Google Sheet name
# Selenium setup
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-logging")
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=chrome_options)

# Function to scrape data
def extract_data_by_label(driver, labels):
    data = {}
    wait = WebDriverWait(driver, 10)
    for label in labels:
        try:
            label_element = wait.until(
                EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{label}')]"))
            )
            data_element = label_element.find_element(By.XPATH, "following-sibling::span[@class='dataContent']")
            data[label] = data_element.text.strip()
        except Exception as e:
            print(f"Error extracting data for label '{label}': {e}")
            data[label] = None
    return data

# Main function
def scrape_and_store():
    driver.get("https://provider.ucare.org/pages/login.aspx")
    print('Going to the website..')

    # Input username and password
    username = driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_bc96337e_dcf6_4453_8de3_e8b322788aea_ctl00_UserName")
    username.send_keys("YOUR-USERNAME")
    password = driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_bc96337e_dcf6_4453_8de3_e8b322788aea_ctl00_Password")
    password.send_keys("YOUR-PASSWORD")
    login_button = driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_bc96337e_dcf6_4453_8de3_e8b322788aea_ctl00_LoginButton")
    login_button.click()
    print('Logging in..')

    time.sleep(5)
    last_n = ['Mohamed', 'Ahmed', 'Ali', 'Hassan', 'Abdullahi', 'Abdul', 'Omar', 'Jama', 'Abdi', 'Abdirahman']
    total_names = len(last_n)
    scrape_limit = random.randint(75, 110)  # Random number of scrapes per day
    current_scrape_count = 0
    print(f"Today's scrape limit: {scrape_limit} records")

    for n in range(total_names):
        if current_scrape_count >= scrape_limit:
            break
        for yr in range(1950, 2007):
            if current_scrape_count >= scrape_limit:
                break
            print(f'Extracting info for Year {yr} - Name: {last_n[n]}')
            driver.get("https://provider.ucare.org/Member%20Information/Pages/eligibility.aspx")
            time.sleep(7)
            last_name = driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_0720f483_9d8a_4be8_9135_30134172db3e_tbLastName")
            last_name.send_keys("Mohamed")
            dob = driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_0720f483_9d8a_4be8_9135_30134172db3e_tbDobField")
            dob.send_keys(f"01/01/{yr}")
            find_button = driver.find_element(By.NAME, "ctl00$SPWebPartManager1$g_0720f483_9d8a_4be8_9135_30134172db3e$ctl06")
            find_button.click()
            time.sleep(5)
            dropdown = Select(driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_0720f483_9d8a_4be8_9135_30134172db3e_ddlMember"))
            total = len(dropdown.options)
            for index in range(len(dropdown.options)):
                if current_scrape_count >= scrape_limit:
                    break
                if index == 0:
                    continue
                print(f'Extracting {index}/{total}')
                dropdown = Select(driver.find_element(By.ID, "ctl00_SPWebPartManager1_g_0720f483_9d8a_4be8_9135_30134172db3e_ddlMember"))
                dropdown.select_by_index(index)
                display_results_button = driver.find_element(By.NAME, "ctl00$SPWebPartManager1$g_0720f483_9d8a_4be8_9135_30134172db3e$ctl07")
                display_results_button.click()

                eligibility = ''
                member_name = ''
                member_number = ''
                pmi_number = ''
                address_1 = ''
                address_2 = ''
                city = ''
                state = ''
                zip_code = ''
                dob = ''
                phone = ''

                wait = WebDriverWait(driver, 10)
                try:
                    eligibility = driver.find_element(By.XPATH, "//h2[contains(text(),'Member is')]").text
                except:
                    pass
                
                div_elements = wait.until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'displayLabelwContent'))
                )
                for div in div_elements:
                    try:
                        data_label_element = div.find_element(By.CLASS_NAME, 'dataLabel')
                        label_text = data_label_element.text.strip()
                        data_content_element = div.find_element(By.CLASS_NAME, 'dataContent')
                        if 'Member Name' in label_text:
                            member_name = data_content_element.text.strip()
                        elif 'Member Number' in label_text:
                            member_number = data_content_element.text.strip()
                        elif 'PMI' in label_text:
                            pmi_number = data_content_element.text.strip()
                        elif 'Address 1' in label_text:
                            address_1 = data_content_element.text.strip()
                        elif 'Address 2' in label_text:
                            address_2 = data_content_element.text.strip()
                        elif 'City' in label_text:
                            city = data_content_element.text.strip()
                        elif 'State' in label_text:
                            state = data_content_element.text.strip()
                        elif 'Zip' in label_text:
                            zip_code = data_content_element.text.strip()
                        elif 'Date of Birth' in label_text:
                            dob = data_content_element.text.strip()
                        elif 'Phone' in label_text:
                            phone = data_content_element.text.strip()
                    except Exception as e:
                        print(f"Error processing a div element: {e}")

                # Add data to Google Sheet
                row_data = [yr, eligibility, member_name, member_number, pmi_number, address_1, address_2, city, state, zip_code, dob, phone]
                sheet.append_row(row_data)

                current_scrape_count += 1
                find_button = driver.find_element(By.NAME, "ctl00$SPWebPartManager1$g_0720f483_9d8a_4be8_9135_30134172db3e$ctl06")
                find_button.click()
                time.sleep(2)
            print(f'Finished year {yr}')

# Run the scraping process
scrape_and_store()
# Wait for 1 day (86400 seconds) before executing again
print("Scraping completed. Waiting for 24 hours before next execution.")
time.sleep(86400)

# Close the WebDriver
driver.quit()
