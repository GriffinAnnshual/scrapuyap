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
from bs4 import BeautifulSoup, NavigableString, Tag

API_KEY = ''  # 2Captcha API key
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
    driver.switch_to.default_content()  # Ana içeriğe dön
    recaptcha_response_element = driver.find_element(By.CLASS_NAME, "rc-anchor-content")
    driver.execute_script("arguments[0].style.display = 'block';", recaptcha_response_element)
    driver.execute_script(f'arguments[0].innerHTML = "{captcha_solution}";', recaptcha_response_element)
    time.sleep(1)
    
    driver.execute_script('document.getElementById("recaptcha-submit").click()')

def human_like_actions(driver):
    time.sleep(random.uniform(1, 3))
    body = driver.find_element(By.TAG_NAME, 'body')
    body.click()
    time.sleep(random.uniform(1, 3))

def process_line(line, pageurl):
    driver = setup_driver()
    try:
        driver.get(pageurl)
        human_like_actions(driver)

       
        is_display_captcha_element = driver.find_element(By.ID, "isDisplayCaptcha")
        is_display_captcha = is_display_captcha_element.get_attribute("innerHTML").strip().lower() == "true"
        if is_display_captcha:
            print("CAPTCHA detected, solving...")

            
            captcha_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
            driver.switch_to.frame(captcha_iframe)

            
            sitekey = driver.find_element(By.CSS_SELECTOR, 'div.g-recaptcha').get_attribute('data-sitekey')

            
            recaptcha_checkbox = driver.find_element(By.CLASS_NAME, "recaptcha-checkbox-border")
            recaptcha_checkbox.click()
            time.sleep(2)  
            
            
            request_id = solve_captcha(driver, sitekey, pageurl)
            captcha_solution = get_captcha_solution(request_id)
            driver.switch_to.default_content()  # Ana içeriğe dön
            apply_captcha_solution(driver, captcha_solution)

        search_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "aranan"))
        )
        search_field.send_keys(Keys.CONTROL, 'a')
        search_field.send_keys(Keys.DELETE)
        search_field.send_keys(line.strip())
        search_field.send_keys(Keys.RETURN)

        wait_for_table_to_load(driver)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', attrs={'class': 'table table-hover dt-responsive dataTable no-footer dtr-inline'})
        
        if table is None:
            print("couldn't find table.")
            return

        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        data = []
        
        for row in rows:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])
        
        hilal = 1
        while hilal < 6 and hilal <= len(data):
            print(hilal)
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
            
            file_name = data[hilal - 1][1].replace('/', ' ') + " " + data[hilal - 1][2].replace('/', ' ')
            with open(f'{file_name}.txt', 'w', encoding='utf-8') as esas:
                for satir in satirlar:
                    esas.write(satir)
                    esas.write('\n')
            hilal += 1
    except Exception as e:
        print(f"error: {e}")
    finally:
        driver.quit()  

def wait_for_table_to_load(driver):
    try:
        
        WebDriverWait(driver, 400).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'table'))
        )
    except Exception as e:
        print(f"error while loading data table: {e}")

with open('TMK.txt', 'r', encoding="utf-8") as tmk:
    pageurl = "https://emsal.uyap.gov.tr/#"
    for line in tmk.readlines():
        process_line(line, pageurl)
