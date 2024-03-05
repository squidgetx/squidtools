from urllib.parse import urljoin, urlparse
from .webscraper import WebScraper, sleep_rnd
from .util import print_err
from .names import simpleMatchScore

from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

class LinkedInNotFound(Exception):
    pass

class LinkedInPageNotRecognized(Exception):
    pass


def guess_linkedin_profile(scraper, name, extra):
    search_string = f"{name} {extra}"
    search_string_escaped = search_string.replace(" ", "%20")
    search_url = f"https://www.linkedin.com/search/results/all/?keywords={search_string_escaped}&origin=GLOBAL_SEARCH_HEADER"
    print(search_url)
    scraper.nav(search_url)

    # Switch to the people tab
    people_btn = scraper.find_element(
        f"//nav//button[text()='People']"
    )
    if people_btn:
        people_btn.click()
        sleep_rnd(2)
    else:
        raise LinkedInPageNotRecognized

    url = None
    # First try to see if there is an exact name match
    result_nodes = scraper.find_elements(
        f"//div[contains(@class,'entity-result')]//a"
    )
    name_nodes = [(n, simpleMatchScore(name, n.getAttribute('innerText'))) for n in result_nodes]
    if len(name_nodes) == 0:
        # No results
        return None
    best = max(name_nodes, key= lambda x: x[1])
    if best[1] < 0.5:
        return None

    url = best.get_attribute('href') 
    return urljoin(url, urlparse(url).path)


def scrape_linkedin_details(scraper, detail_url):
    scraper.nav(detail_url)
    expand_about = scraper.driver.find_elements(By.CLASS_NAME, "inline-show-more-text__button")
    for ele in expand_about:
        if "see more" in ele.text:
            ele.click()
    html = scraper.driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    div = soup.find("main")
    details = []
    if div and "Nothing to see" not in div.text and div.find('ul'):
        ul = div.find("ul")
        detail_lis = ul.findChildren("li", recursive=False)
        for li in detail_lis:
            header = li.select_one('div.flex-row')
            title = getText(header.select_one('.t-bold > span'))
            subtitle = getText(header.select_one('.t-normal > span'))
            time = getText(header.select_one('.t-black--light > span'))

            extra_details_parent = li.select_one('div.pvs-list__container')
            extra_detail_text = None
            if extra_details_parent:
                extra_details = extra_details_parent.select('ul.pvs-list > li')
                if len(extra_details) > 1:
                    # Weird linked in nested thing
                    titles = [getText(e.select_one('.t-bold > span')) for e in extra_details]
                    times = [getText(e.select_one('.t-black--light > span')) for e in extra_details]
                    main_title = titles[0]
                    titles_texts = ','.join((t for t in titles if t))
                    time_texts = ','.join((t for t in times if t))
                    time = subtitle
                    subtitle = title
                    title = main_title
                    extra_detail_text = {
                        'titles': titles_texts,
                        'times': time_texts,
                    }
                else:
                    extra_detail_text = '\n'.join((getText(e.select_one('span')) for e in extra_details if e.select_one('span')))

            details.append({
                'title': title,
                'subtitle': subtitle,
                'time': time,
                'extra_details': extra_detail_text
            })
    return details

def getText(node):
    if node:
        return node.getText(separator=" ", strip=True)
    return None


def scrape_linkedin_profile(scraper, url):
    scraper.nav(url)
    expand_about = scraper.driver.find_elements(By.CLASS_NAME, "inline-show-more-text__button")
    for ele in expand_about:
        if "see more" in ele.text:
            ele.click()
    html = scraper.driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    header = main.find("section")

    li_name = getText(header.find("h1"))
    current_spans = header.select("span.text-body-small.hoverable-link-text")
    pronoun_span = header.select_one("span.text-body-small.v-align-middle:not(.distance-badge)")
    location_span = header.select_one("div.mt2 > span.text-body-small")
    pronouns = getText(pronoun_span)
    location = getText(location_span)
    title = getText(header.find('div', class_="text-body-medium"))
    about = getText(main.find('div', id='about'))
    current = ','.join([getText(cs) for cs in current_spans])


    educations = scrape_linkedin_details(scraper, url + "/details/education")
    experiences = scrape_linkedin_details(scraper, url + "/details/experience")

    return {
        "url": url,
        "li_name": li_name,
        "pronouns": pronouns,
        'title': title,
        "about": about,
        "location": location,
        'current': current,
        "experience": experiences,
        "education": educations,
    }

class LinkedInScraper(WebScraper):

    def __init__(self, username, password, delay=4):
        WebScraper.__init__(self, delay)

        # manual log in
        AUTH_URL = "https://www.linkedin.com/"
        self.nav(AUTH_URL)
        self.find_element(
            f"//input[@autocomplete='username']"
        ).send_keys(username)
        self.find_element(
            f"//input[@autocomplete='current-password']"
        ).send_keys(password)
        
        print_err("Press enter once login is complete...")
        input("")
    
    def scrape(self, name, desc, url=None):
        if url is None:
            url = guess_linkedin_profile(self, name, desc)
        if url is None:
            raise LinkedInNotFound
        results = scrape_linkedin_profile(self, url)
        return results