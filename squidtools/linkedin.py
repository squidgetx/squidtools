from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


from bs4 import BeautifulSoup
import random
import time

from urllib.parse import urljoin, urlparse


class LinkedInNotFound(Exception):
    pass

class LinkedInSetupRequired(Exception):
    pass

class LinkedInPageNotRecognized(Exception):
    pass

def sleep_rnd(base=5):
    time.sleep(random.random() * base + base)

class LinkedInScraper():
    driver = None

    def __init__(self, username, password):
        self.driver = webdriver.Chrome()
        AUTH_URL = "https://www.linkedin.com/"
        self.driver.get(AUTH_URL)
        time.sleep(2)
        userfield = self.driver.find_element(
            By.XPATH, f"//input[@autocomplete='username']"
        )
        userfield.send_keys(username)
        passfield = self.driver.find_element(
            By.XPATH, f"//input[@autocomplete='current-password']"
        )
        passfield.send_keys(password)
        
        # manual log in
        input("Press enter once login is complete...")

    def try_linkedin(self, name, extra):
            url = self.guess_linkedin_profile(name, extra)

            if url:
                return self.scrape_linkedin_profile(url)
            else:
                raise LinkedInNotFound

    def guess_linkedin_profile(self, name, extra):
        search_string = f"{name} {extra}"
        search_string_escaped = search_string.replace(" ", "%20")
        search_url = f"https://www.linkedin.com/search/results/all/?keywords={search_string_escaped}&origin=GLOBAL_SEARCH_HEADER&sid=w7v"
        self.driver.get(search_url)
        sleep_rnd()

        # Switch to the people tab
        people_btn = self.driver.find_element(
            By.XPATH, f"//nav//button[text()='People']"
        )
        if people_btn:
            people_btn.click()
            sleep_rnd()
        else:
            raise LinkedInPageNotRecognized

        url = None
        # First try to see if there is an exact name match
        result_nodes = self.driver.find_elements(
            By.XPATH, f"//div[contains(@class,'entity-result')]//a"
        )
        name_nodes = [n for n in result_nodes if name in n.get_attribute("innerText")]
        if len(name_nodes) > 0:
            url = name_nodes[0].get_attribute("href")
        else:
            # If there's no exact name match, (possibly because of middle names and such)
            # get the first link that has at least one submatch
            name_pieces = [n for n in name.split(" ") if len(n) > 1]
            name_nodes = [
                n
                for n in result_nodes
                if any([x.lower() in n.get_attribute("innerText").lower() for x in name_pieces])
            ]
            if len(name_nodes) > 0:
                url = name_nodes[0].get_attribute("href")
            else:
                return None

        return urljoin(url, urlparse(url).path)


    def scrape_linkedin_details(self, detail_url):
        self.driver.get(detail_url)
        sleep_rnd()
        expand_about = self.driver.find_elements(By.CLASS_NAME, "inline-show-more-text__button")
        for ele in expand_about:
            if "see more" in ele.text:
                ele.click()
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        div = soup.find(id="main")
        details = []
        if div and "Nothing to see" not in div.text:
            ul = div.find("ul")
            detail_lis = ul.findChildren("li", recursive=False)
            for li in detail_lis:
                info = li.find(class_="flex-row").find_all("span", {"aria-hidden": True})
                details.append([i.getText(strip=True) for i in info])
        return details


    def scrape_linkedin_profile(self, url):
        self.driver.get(url)
        sleep_rnd()
        expand_about = self.driver.find_elements(By.CLASS_NAME, "inline-show-more-text__button")
        for ele in expand_about:
            if "see more" in ele.text:
                ele.click()
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main")
        li_name = soup.find("h1").getText() if soup.find("h1") else None
        pronoun_span = main.find("span", class_="text-body-small")
        pronouns = None
        if pronoun_span:
            pronouns = pronoun_span.getText(separator=" ", strip=True)

        about = soup.find(id="about")
        if about:
            about = about.parent.getText(separator=" ", strip=True)

        educations = self.scrape_linkedin_details(url + "/details/education")
        experiences = self.scrape_linkedin_details(url + "/details/experience")

        return {
            "li_name": li_name,
            "url": url,
            "pronouns": pronouns,
            "about": about,
            "experience": experiences,
            "education": educations,
        }

