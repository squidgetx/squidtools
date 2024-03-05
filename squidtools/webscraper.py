import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import random

# Sleep for a random amount of time 
# in uniform interval 0.5*base and 1.5*base
def sleep_rnd(base=5):
        time.sleep((random.random() * base + base) * 0.5)

class WebScraper:
    driver = None
    delay = 2
    
    def nav(self, url):
        self.driver.get(url)
        sleep_rnd(self.delay)


    def find_element(self, xpath):
        try:
            return self.driver.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            return None

    def find_elements(self, xpath):
        return self.driver.find_elements(By.XPATH, xpath)

    def find_element_text(self, xpath):
        ele = self.find_element(xpath)
        if ele:
            return ele.text
        else:
            return None


    def find_element_attr(self, xpath, attr):
        ele = self.find_element(xpath)
        if ele:
            return ele.get_attribute(attr)
        else:
            return None

    def __init__(self, delay=2):
        self.driver = uc.Chrome()
        self.delay = delay
