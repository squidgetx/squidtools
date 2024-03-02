# Code to get extra data about a given writer
# If all we have is information about their name and outlet
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

import undetected_chromedriver as uc
import random
import math
import string
import time
import Levenshtein

from .util import print_err

class MuckrackProfileNotFound(Exception):
    pass

class RateLimitError(Exception):
    pass

def find_element(driver, xpath):
    try:
        return driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return None

def find_element_text(driver, xpath):
    ele = find_element(driver, xpath)
    if ele:
        return ele.text
    else:
        return None
    
def unnormalize_name(name):
    if ',' in name:
        names = name.split(',')
        joined = ' '.join(names[1:] + [names[0]])
        return joined.replace('  ', ' ').strip()
    return name

def l_distance_names(name1, name2):
    name1 = unnormalize_name(name1).lower().translate(str.maketrans('', '', string.punctuation))
    name2 = unnormalize_name(name2).lower().translate(str.maketrans('', '', string.punctuation))
    return Levenshtein.distance(name1, name2)

def clean(name):
    return name.lower().translate(str.maketrans('', '', string.punctuation))



def find_profile_ddf(driver, name, newspaper):
    search_string = f"site%3Amuckrack.com {name} {newspaper}"
    search_string_escaped = search_string.replace(" ", "%20")
    search_url = f"http://duckduckgo.com/?q=!ducky+{search_string_escaped}"
    driver.get(search_url)
    time.sleep(1.5)
    url = driver.current_url
    if 'muckrack.com' not in url:
        return None
    return url

def find_profile_helper(driver, name, search_url, attempts=0):
    driver.get(search_url)
    time.sleep(1)
    match = find_element(driver, '//div[contains(@class,"mr-result-content")]//h5[contains(@class,"mr-result-heading")]/a[b]')
    if match:
        return match.get_attribute('href')
    matches = driver.find_elements(
        By.XPATH, 
        '//div[contains(@class,"mr-result-content")]//h5[contains(@class,"mr-result-heading")]/a'
    )
    # Sometimes the match isn't bolded, but it should still have the 
    # name match basically
    if len(matches) > 0:
        names = [clean(n) for n in name.split(" ") if len(clean(n)) > 1]
        for match in matches:
            if all((n in match.text.lower() for n in names)):
                return match.get_attribute('href')

    if find_element(driver, '//*[contains(text(), "Rate limited")]'):
        # We got rate limited
        sleeptime = math.exp(attempts) * 8
        print_err(f"Rate limited! Sleeping for {sleeptime}s")
        time.sleep(sleeptime)
        return find_profile_helper(driver, name, search_url, attempts + 1)

    return None


def find_profile(driver, name, newspaper):
    # First query muckrack with the name + newspaper
    search_query = f"{name} {newspaper}".replace(' ', '+')
    search_url=f"https://muckrack.com/search/results?q={search_query}&result_type=person&search_source=homepage"
    url = find_profile_helper(driver, name, search_url)
    if url:
        return url

    # Then query muckrack with the name only
    search_query = f"{name}".replace(' ', '+')
    search_url=f"https://muckrack.com/search/results?q={search_query}&result_type=person&search_source=homepage"
    url = find_profile_helper(driver, name, search_url)
    if url:
        return url
    
    # Finally, query ddg
    url = find_profile_ddf(driver, name, newspaper)
    if url:
        return url
    
    raise MuckrackProfileNotFound


def scrape_profile(driver, name, newspaper, delay=8):
    
    time.sleep(random.random() * delay)

    url = find_profile(driver, name, newspaper)
    driver.get(url)
    time.sleep(random.random() * delay)
   
    # First try to see if there is an exact name match
    mr_name = find_element_text(driver, f"//h1[contains(@class,'profile-name')]")
    mr_location = find_element_text(driver, f"//div[contains(@class,'person-details-location')]")
    if mr_name is None:
        return None
    more_link = find_element(driver, f"//a[contains(@class, 'as-seen-in-more')]")
    if more_link:
        more_link.click()
        time.sleep(0.5)
    mr_details = find_element_text(driver, f"//div[contains(@class,'profile-details-item')]")

    twitter = find_element(driver, f"//div[@class='profile-section-social']/a[contains(@class, 'js-icon-twitter')]")
    twitter_link = twitter.get_attribute('href') if twitter else None
    website = find_element(driver, f"//div[@class='profile-section-social']/a[contains(@class, 'js-icon-link')]")
    website_link = website.get_attribute('href') if website else None
    linkedin = find_element(driver, f"//div[@class='profile-section-social']/a[contains(@class, 'js-icon-linkedin')]")
    linkedin_link = linkedin.get_attribute('href') if linkedin else None

    details_match = newspaper.lower() in mr_details.lower() if mr_details else False
    name_lev_distance = l_distance_names(mr_name, name)
    lev_score = math.exp(-name_lev_distance/4)
    match_confidence = (int(details_match) + lev_score) / 2
    return {
        'name': mr_name,
        'details': mr_details,
        'location': mr_location,
        'twitter': twitter_link,
        'website': website_link,
        'linkedin_link': linkedin_link,
        'name_lev_distance': name_lev_distance,
        'lev_score': lev_score,
        'detail_match': details_match,
        'match_confidence': match_confidence,
        'url': url,
    }

class MuckrackScraper():
    driver = None

    def __init__(self, username, password):
        self.driver = uc.Chrome()
        self.driver.get('https://muckrack.com/account/login/')
        time.sleep(1)
        find_element(self.driver, '//input[@id="id_auth-username"]').send_keys(username)
        find_element(self.driver, '//input[@id="id_auth-password"]').send_keys(password)
        input("Press enter once login is successful")
    
    def scrape(self, name, outlet, delay=10):
        return scrape_profile(self.driver, name, outlet, delay)

