import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

KEYWORDS = ["junior developer", "fullstack", "backend", "frontend"]

# FIREFOX_PROFILE_PATH = "/Users/zviatos/Library/Application Support/Firefox/Profiles/l0tx736r.default-release"
CHROME_USER_DATA_DIR = "/Users/zviatos/Library/Application Support/Google/Chrome"
CHROME_PROFILE = "Profile 1"  

def main():
    username = ""
    password = ""
    opts = browser_setup()
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=opts)
    # TODO: Add the functionality to load with existing profile data without crashing
    login(browser, username, password)
    start_apply(browser)

def human_delay(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def browser_setup():
    # -------- Configure Firefox Profile --------
    # opts = Options()
    # opts.profile = FIREFOX_PROFILE_PATH


    # -------- Configure Chrome Profile --------
    opts = webdriver.ChromeOptions()

    # opts.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    # opts.add_argument(f"--profile-directory={CHROME_PROFILE}")

    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    # Can be useful on Mac to disable GPU
    opts.add_argument("--disable-gpu")
    opts.add_argument("--remote-debugging-port=9222")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    opts.add_experimental_option('useAutomationExtension', False)


    print("Chrome options configured.")
    return opts

def login(browser, username,password):
    browser.get("https://www.linkedin.com/login")
    try:
            user_field = browser.find_element("id","username").send_keys(username)
            # user_field = browser.find_element(By.ID,"username").send_keys(username)
            pw_field = browser.find_element("id","password").send_keys(password)
            time.sleep(2)
            login_button = browser.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(15)
    except Exception as e:
           print(f" Username/password field or login button not found, {e}")

def start_apply(browser):

    try:
        for keyword in KEYWORDS:
            print(f"Searching for jobs with keyword: {keyword}")
            
            browser.get(f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location=Madrid%2C%20Spain") 
            human_delay(3, 7)
            # TODO: Finish the logic of job application
            # Lisf of jobs
            links = browser.find_element("xpath", "//div[@data-job-id]")
            print(f"Processing job listing: {links}")

            for job in links:
                try:
                    # Scroll to the job listing to make it visible
                    browser.execute_script("arguments[0].scrollIntoView();", job)
                    human_delay(1, 3)

                    # job_title_element = job.find_element(By.CSS_SELECTOR, "a.job-card-list__title")
                    # job_title_element.click()
                    # human_delay(2, 5)

                    # "Easy Apply" button
                    easy_apply_button = browser.find_element("xpath",'//button[contains(@class, "jobs-apply-button")]')
                    easy_apply_button.click()
                    human_delay(2, 4)
                    
                    # Click "Next" if it exists
                    next_button = browser.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    while next_button:
                        next_button.click()
                        human_delay(2, 5)
                        try:
                            next_button = browser.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                        except:
                            next_button = None

                    # Review and submit
                    review_button = browser.find_element(By.CSS_SELECTOR, "button[aria-label='Review your application']")
                    review_button.click()
                    human_delay(2,5)

                    submit_button = browser.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                    submit_button.click() # Uncomment to actually submit
                    print("Application submitted (simulation).")


                    # For now, just close the application modal to continue to the next job
                    close_button = browser.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
                    close_button.click()
                    human_delay(1, 2)

                except Exception as e:
                    print(f"Could not process a job listing: {e}")
                    try:
                        close_button = browser.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
                        close_button.click()
                        human_delay(1, 2)
                    except:
                        pass

    except Exception as e:
        print(f"Could not complete the search for keyword '{keyword}': {e}")

    # TODO: AI integration for cover letter generation or custome responses
    
    # Close browser after some time
    browser.quit()


if __name__ == "__main__":
    main()