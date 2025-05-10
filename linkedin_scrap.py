import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_recaptcha_solver import RecaptchaSolver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from urllib.parse import urlparse, parse_qs
import pickle
import random
import time
import toml
import os
import sys
from main_logging import logging_func,logging
class WebScraper:
    def __init__(self):
        self.driver = None
        self.cfg = None
        self.found = False
        self.mp = ""
        self.init_configs()
        self.init_driver()
        
    def __del__(self):
        if self.driver:
            self.cleanup_driver()
 
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.cleanup_driver()
    
    @logging_func
    def init_configs(self):
        try:
            for root, _, files in os.walk("./"):
                for f in files:
                    if f.endswith(".toml"):
                        self.found = True
                        self.mp = os.path.join(root, f)
                        break
                if self.found:
                    break

            if not self.found:
                print("Error: Cannot find config.toml. Please make a config.toml in the same directory.")
                sys.exit(1)

            with open(self.mp, "r") as f:
                self.cfg = toml.load(f)

            if "job_platform_config" not in self.cfg:
                raise ValueError("Missing [job_platform_config] section in config.toml")
            if "job_platform_config" not in self.cfg:
                raise ValueError("Missing [job_platform_config] section in config.toml")

            for key in ["url", "signin_url"]:
                val = self.cfg["job_platform_config"].get(key)
                if not val or str(val).strip() == "":
                    raise ValueError(f"Missing or empty '{key}' in [job_platform_config] section")
            if not self.cfg["job_platform_config"]["url"]:
                raise ValueError("Error: Array of url is empty in toml")

            for key in ["email", "password"]:
                val = self.cfg["credentials"].get(key)
                if not val or str(val).strip() == "":
                    raise ValueError(f"Missing or empty '{key}' in [credentials] section")

            print("✅ Config loaded and validated successfully!")
            logging.info("config load sucess ✅")
        except Exception as e:
            print(f"❌ Failed to load or validate config.toml: {e}")
            sys.exit()
    @logging_func
    def init_driver(self):
        if not self.driver:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")

            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')

            self.driver = uc.Chrome(options=options)
            self.driver.set_window_size(random.randint(1200, 1600), random.randint(800, 1000))
    @logging_func
    def cleanup_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                print("🛑 Browser closed successfully")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")
            finally:
                self.driver = None  # Ensure dereference

    def random_delay(self, min_time=1.5, max_time=4.0):
        time.sleep(random.uniform(min_time, max_time))

    def handle_captcha(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title*='Cloudflare Challenge']"))
            )

            solver = RecaptchaSolver(driver=self.driver)
            solver.click_recaptcha_v2(
                iframe=self.driver.find_element(By.CSS_SELECTOR, "iframe[title*='Cloudflare Challenge']")
            )

            self.driver.switch_to.default_content()
            return True
        except Exception as e:
            print(f"CAPTCHA handling failed: {e}")
            return False
    @logging_func
    def get_job_data(self):
        try:
        
            # Wait for initial jobs to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-entity-urn^='urn:li:jobPosting']"))
            )
            logging.info("LinkedIn loaded successfully")
            print("LinkedIn load success!!")

            last_count = 0
            max_attempts = 5
            attempts = 0
         
            while attempts < max_attempts:
                # Scroll to bottom to trigger loading
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)  # Short sleep for scroll action

                # Try to click "See more jobs" button if exists
                try:
                    see_more_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='See more jobs']"))
                    )
                    self.driver.execute_script("arguments[0].click();", see_more_button)
                    print("Clicked 'See more jobs' button")
                    # Wait for new content to load after click
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-entity-urn^='urn:li:jobPosting']"))
                    )
                    attempts = 0  # Reset counter if new content loaded
                except (TimeoutException, ElementNotInteractableException):
                    pass

                # Get current job count
                current_jobs = self.driver.find_elements(By.CSS_SELECTOR, "div[data-entity-urn^='urn:li:jobPosting']")
                current_count = len(current_jobs)

                # Check if we've stopped loading new jobs
                if current_count == last_count:
                    attempts += 1
                else:
                    attempts = 0
                    last_count = current_count

                print(f"Current job count: {current_count}")

            # Final collection of all loaded jobs
            all_jobs = self.driver.find_elements(By.CSS_SELECTOR, "div[data-entity-urn^='urn:li:jobPosting']")
            print(f"Total jobs found: {len(all_jobs)}")
            for job in all_jobs:
                try:
                    curl=self.driver.current_url
                    # Titleclass="sr-only"
                    title = job.find_element(By.CLASS_NAME, "sr-only").text.strip()

                    # URL
                    url = job.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")

                    # Company name
                    company = job.find_element(By.CLASS_NAME, "base-search-card__subtitle").text.strip()

                    # Posted time
                    posted_time = job.find_element(By.CLASS_NAME, "job-search-card__listdate").text.strip()
                    location = job.find_element(By.CLASS_NAME, "job-search-card__location").text.strip()

                    yield {
                    "main_url":curl,
                    "title":title,
                     "url":url,
                     "company_name":company,
                     "posted_time":posted_time,
                     "location":location
                    }
                    # print(f"Title: {title}")
                    # print(f"URL: {url}")
                    # print(f"Company: {company}")
                    # print(f"Posted: {posted_time}\n")

                except Exception as e:
                    print(f"Error extracting job info: {e}")
                    continue
             
        except Exception as e:
            print(f"🔥 Error in job scraping: {str(e)}")
            logging.error(f"Job scraping failed: {str(e)}")
            self.cleanup_driver()
            return []
    @logging_func
    def get_jobs(self):
        try:
            self.init_driver() 
            for url in self.cfg["job_platform_config"]["url"]:
                try:
              
                    print(f"🎯 Applying for position at job: {url}")
                    self.driver.get(url)
                    #self.random_delay(2, 3)

                    for _ in range(random.randint(2, 4)):
                        try:
                            ActionChains(self.driver)\
                                .scroll_by_amount(0, random.randint(300, 800))\
                                .pause(random.uniform(0.8, 1.2))\
                                .perform()
                        except Exception as scroll_error:
                            print(f"⚠️ Scrolling failed: {scroll_error}")
                            continue

                    for jd in self.get_job_data():
                        yield jd
                   

                except Exception as page_error:
                    print(f"⚠️ Error processing URL {url}: {page_error}")
                    continue

 

        finally:
            self.cleanup_driver()
            time.sleep(random.randint(2, 5))

 
