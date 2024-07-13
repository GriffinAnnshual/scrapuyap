from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import time
import random
import requests
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup, NavigableString, Tag
import re
import os
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("API_KEY")  # 2Captcha API key

def setup_driver():
    ua = UserAgent()
    user_agent = ua.random
    print(f"Kullanıcı Ajanı: {user_agent}")
    options = Options()
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-web-security')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def solve_captcha(driver, sitekey, pageurl):
    response = requests.post("http://2captcha.com/in.php", data={
        'key': API_KEY,
        'method': 'userrecaptcha',
        'googlekey': sitekey,
        'pageurl': pageurl,
        'json': 1
    })
    request_id = response.json().get('request')
    return request_id

def get_captcha_solution(request_id):
    url = f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={request_id}&json=1"
    while True:
        time.sleep(5)
        response = requests.get(url)
        if response.json().get('status') == 1:
            return response.json().get('request')
        print("CAPTCHA solving...")

def apply_captcha_solution(driver, captcha_solution):
    driver.switch_to.default_content()  # Switch back to the main content

    try:
        recaptcha_response_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "g-recaptcha-response"))
        )
        driver.execute_script("arguments[0].style.display = 'block';", recaptcha_response_element)
        driver.execute_script(f'arguments[0].value = "{captcha_solution}";', recaptcha_response_element)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Page source:")
        print(driver.page_source)

    time.sleep(2)

def human_like_actions(driver):
    time.sleep(random.uniform(1, 3))
    body = driver.find_element(By.TAG_NAME, 'body')
    body.click()
    time.sleep(random.uniform(1, 3))

def sanitize_file_name(file_name):
    # Remove invalid characters from the file name
    file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
    return file_name

def process_line(line, pageurl):
    print("Process started...")
    driver = setup_driver()
    try:
        driver.get(pageurl)
        human_like_actions(driver)
    
        
        
        # Try to find the CAPTCHA element and get its sitekey
        try:
            is_display_captcha_element = driver.find_element(By.CLASS_NAME, "g-recaptcha")
            sitekey = is_display_captcha_element.get_attribute('data-sitekey')
        except Exception as e:
            is_display_captcha_element = None # skips the captcha process


        """
        -> Uncomment the below code and comment above one to test captcha functionality!

        while True:
            print("Trying to find CAPTCHA element...")
            time.sleep(1)
            try:
                # Locate the CAPTCHA element by class name
                is_display_captcha_element = driver.find_element(By.CLASS_NAME, "g-recaptcha")
                sitekey = is_display_captcha_element.get_attribute('data-sitekey')
                if is_display_captcha_element:
                    print("CAPTCHA element found.")
                    print(is_display_captcha_element.get_attribute('data-sitekey'))
                    break
            except Exception as e:
                continue

        """

        
        # If CAPTCHA element is found, solve the CAPTCHA
        if is_display_captcha_element:
            print("CAPTCHA detected, solving...")

            # Find and switch to the CAPTCHA iframe
            try:
                captcha_iframe = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
                )
                driver.switch_to.frame(captcha_iframe)
                print("Switched to CAPTCHA iframe.")
            except Exception as e:
                print("Error: CAPTCHA iframe not found.")
                return

            # Wait for the CAPTCHA checkbox to be present and clickable
            try:
                recaptcha_checkbox = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border"))
                )
                recaptcha_checkbox.click()
                print("CAPTCHA checkbox clicked.")
                time.sleep(2)
            except Exception as e:
                print("Error: CAPTCHA checkbox not found or not clickable.")
                return

            # Solve the CAPTCHA and apply the solution
            request_id = solve_captcha(driver, sitekey, pageurl)
            captcha_solution = get_captcha_solution(request_id)
            driver.switch_to.default_content()
            apply_captcha_solution(driver, captcha_solution)
        
        # Wait for the search field to be present and perform the search
        search_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "aranan"))
        )
        search_field.send_keys(Keys.CONTROL, 'a')
        search_field.send_keys(Keys.DELETE)
        search_field.send_keys(line.strip())
        search_field.send_keys(Keys.RETURN)

        wait_for_table_to_load(driver)
        
        # Parse the page source with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'detayAramaSonuclar'})
        if table is None:
            print("Couldn't find table.")
            return

        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        data = []
        
        # Extract table data
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])
        
        # Iterate over the data and process each row
        hilal = 1
        while hilal < 6 and hilal <= len(data):
            element = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.ID, str(hilal)))
            )
            element.click()
            time.sleep(0.5)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            satirlar = []
            for br in soup.findAll('br'):
                next_s = br.nextSibling
                if not (next_s and isinstance(next_s, NavigableString)):
                    continue    
                next2_s = next_s.nextSibling
                if next2_s and isinstance(next2_s, Tag) and next2_s.name == 'br':
                    text = str(next_s).strip()
                    if text:
                        satirlar.append(next_s)
            
            file_name = 'Esas:' + data[hilal - 1][1].replace('/', ' ') + " " + 'Karar:' + data[hilal - 1][2].replace('/', ' ')
            sanitized_file_name = sanitize_file_name(file_name)
            with open(f'{sanitized_file_name}.txt', 'w', encoding='utf-8') as esas:
                for satir in satirlar:
                    esas.write(satir)
                    esas.write('\n')
            print("File Saved: ", file_name + '.txt')
            hilal += 1
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

def wait_for_table_to_load(driver):
    try:
        time.sleep(3)
    except Exception as e:
        print(f"Error while loading data table: {e}")

with open('TMK.txt', 'r', encoding="utf-8") as tmk:
    pageurl = "https://emsal.uyap.gov.tr/#"
    for line in tmk.readlines():
        process_line(line, pageurl)
