from twocaptcha import TwoCaptcha
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import time
import base64
from datetime import datetime
import requests
from PIL import Image

#solver = TwoCaptcha('60418bbe973d1a78964fc1d31cccc8e2')  # Replace with your actual API key

SAVE_DIR = "text_files"  
os.makedirs(SAVE_DIR, exist_ok=True)

# Set up Selenium
chrome_options = Options()
#chrome_options.add_argument('--start-maximized')
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """
})
driver.get("https://karararama.yargitay.gov.tr")
time.sleep(5)

# Step 1: Click "Detaylı Arama"
wait = WebDriverWait(driver, 9)
detayli_arama_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'DETAYLI ARAMA')]")))
detayli_arama_btn.click()

start_date = wait.until(EC.presence_of_element_located(
    (By.XPATH, "//input[@placeholder='Başlama tarihini giriniz.']")))

end_date = wait.until(EC.presence_of_element_located(
    (By.XPATH, "//input[@placeholder='Bitiş tarihini giriniz.']")))

# Use JavaScript to set the date values
driver.execute_script("arguments[0].value = '02.01.2017';", start_date)
driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", start_date)

driver.execute_script("arguments[0].value = '13.06.2025';", end_date)
driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", end_date)

search_btn = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "detaylıAramaG"))
)
search_btn.click()

WebDriverWait(driver, 3).until(
    EC.presence_of_element_located((By.XPATH, "(//table)[1]//tr"))
)

case_count = 1
while True:
    try:
        print(f"[i] Processing case #{case_count}")
        # Wait for the karar text to be loaded via JS
        wait.until(lambda d: d.execute_script("""
            const el = document.querySelector('#kararAlani .card-scroll');
            return el && el.innerText && el.innerText.trim().length > 50;
        """))
        # Extract title and content via JS
        title = driver.execute_script("""
            const h = document.querySelector('div.row h5');
            return h ? h.innerText.trim() : 'Karar';
        """)

        karar_text = driver.execute_script("""
            return document.querySelector('#kararAlani .card-scroll').innerText.trim();
        """)

        filename = f"{case_count:03d}_{title.replace('/', '-').replace(' ', '_')[:80]}.txt"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{karar_text}")

        print(f"[✓] Saved: {filename}")

        # Step 5: Click "Sonraki Karar" button
        try:
            next_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'moveNext')]")
            driver.execute_script("moveNext();")
            time.sleep(2)
        except Exception as e:
            print(f"[i] Couldn't go to next case: {e}")
            break
        case_count += 1
    except Exception as e:
        print(f"[!] Failed to process case #{case_count}: {e}")
        screenshot_path = os.path.join(SAVE_DIR, f"error_{case_count}.png")
        driver.save_screenshot(screenshot_path)
        print(f"[!] Screenshot saved: {screenshot_path}")
        
        input("[🛑] If this is a CAPTCHA, solve it manually in the browser, then press Enter to retry...")
        continue

driver.quit()
print("[✓] Done.")
