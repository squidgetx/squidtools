# Code to get extra data about a given writer
# If all we have is information about their name and outlet

import random
import math
import string
import time

from .util import print_err
from .webscraper import WebScraper
from .names import lev_dist, simpleMatchScore

class MuckrackProfileNotFound(Exception):
    pass

class RateLimitError(Exception):
    pass

def find_profile_ddg(scraper, name, newspaper):
    search_string = f"site%3Amuckrack.com {name} {newspaper}"
    search_string_escaped = search_string.replace(" ", "%20")
    search_url = f"http://duckduckgo.com/?q=!ducky+{search_string_escaped}"
    scraper.nav(search_url)
    url = scraper.driver.current_url
    if 'muckrack.com' not in url:
        return None
    return url

def find_profile_helper(scraper, name, search_url, attempts=0):
    scraper.nav(search_url)
    match = scraper.find_element(
        '//div[contains(@class,"mr-result-content")]//h5[contains(@class,"mr-result-heading")]/a[b]'
    )
    if match:
        return match.get_attribute('href')
    matches = scraper.find_elements(
        '//div[contains(@class,"mr-result-content")]//h5[contains(@class,"mr-result-heading")]/a'
    )

    # Sometimes the match isn't bolded, but it should still have the 
    # name match basically
    if len(matches) > 0:
        name_matches = [(match, simpleMatchScore(name, match.text)) for match in matches]
        best = max(name_matches, key=lambda x: x[1])
        if best[1] > 0.5:
            return best[0].get_attribute('href')

    if scraper.find_element('//*[contains(text(), "Rate limited")]'):
        # We got rate limited
        sleeptime = math.exp(attempts) * 8
        print_err(f"Rate limited! Sleeping for {sleeptime}s")
        time.sleep(sleeptime)
        return find_profile_helper(scraper, name, search_url, attempts + 1)

    return None


def find_profile(scraper, name, newspaper):
    # First query muckrack with the name + newspaper
    search_query = f"{name} {newspaper}".replace(' ', '+')
    search_url=f"https://muckrack.com/search/results?q={search_query}&result_type=person&search_source=homepage"
    url = find_profile_helper(scraper, name, search_url)
    if url:
        return url

    # Then query muckrack with the name only
    search_query = f"{name}".replace(' ', '+')
    search_url=f"https://muckrack.com/search/results?q={search_query}&result_type=person&search_source=homepage"
    url = find_profile_helper(scraper, name, search_url)
    if url:
        return url
    
    # Finally, query ddg
    url = find_profile_ddg(scraper, name, newspaper)
    if url:
        return url
    
    raise MuckrackProfileNotFound


def scrape_profile(scraper, name, newspaper):

    url = find_profile(scraper, name, newspaper)
    scraper.nav(url)
   
    # First try to see if there is an exact name match
    mr_name = scraper.find_element_text(f"//h1[contains(@class,'profile-name')]")
    mr_location = scraper.find_element_text(f"//div[contains(@class,'person-details-location')]")
    if mr_name is None:
        return {
            'url': url,
            'error': "MuckrackProfileParseError"
        }
    more_link = scraper.find_element(f"//a[contains(@class, 'as-seen-in-more')]")
    if more_link:
        more_link.click()
        time.sleep(0.5)
    mr_details = scraper.find_element_text(f"//div[contains(@class,'profile-details-item')]")

    twitter_link = scraper.find_element_attr(
        f"//div[@class='profile-section-social']/a[contains(@class, 'js-icon-twitter')]", 
        'href'
    )
    website_link = scraper.find_element_attr(
        f"//div[@class='profile-section-social']/a[contains(@class, 'js-icon-link')]",
        "href"
    )
    linkedin_link = scraper.find_element_attr(
        f"//div[@class='profile-section-social']/a[contains(@class, 'js-icon-linkedin')]",
        'href'
    )

    details_match = newspaper.lower() in mr_details.lower() if mr_details else False
    return {
        'name': mr_name,
        'details': mr_details,
        'location': mr_location,
        'twitter': twitter_link,
        'website': website_link,
        'linkedin_link': linkedin_link,
        'detail_match': details_match,
        'url': url,
    }

class MuckrackScraper(WebScraper):

    def __init__(self, username, password, delay=8):
        WebScraper.__init__(self, delay)
        self.nav('https://muckrack.com/account/login/')
        self.find_element('//input[@id="id_auth-username"]').send_keys(username)
        self.find_element('//input[@id="id_auth-password"]').send_keys(password)
        print_err("Press enter once login is successful")
        input("")
    
    def scrape(self, name, outlet):
        return scrape_profile(self, name, outlet)

