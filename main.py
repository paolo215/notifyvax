
import requests
import config
import smtplib
import ssl
import sys
import email
import bs4
import datetime
import json

from bs4 import BeautifulSoup
from selenium import webdriver
from email.message import EmailMessage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TIMEOUT = 30

class NotifyVax:

    def __init__(self):
        self.config = config.config
        self.sites = self.config["sites"]

        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("enable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        options.add_argument("disable-features=NetworkService")
        options.page_load_strategy = "normal"
        self.driver = webdriver.Chrome("./driver/chromedriver", chrome_options=options)

    def scan(self):
        ohsu = self.check_ohsu()
        title = "COVID Vaccine Scheduling"
        found = False
        messages = []
        if ohsu:
            messages.append("OHSU vaccination scheduling may be available: " + self.sites["ohsu"])
            found = True


        if found:
            self.send_email(title, "\r\n".join(messages))

    def check_costco(self):
        for s in self.sites["costco"]:
            self.driver.get(s)
            self.driver.implicitly_wait(1)
            h1 = self.driver.find_element_by_css_selector("h1")
            if h1.text != "Account Error":
                return True, s
        return False, None

    def check_albertsons(self):
        site = self.sites["albertsons"]
        self.driver.get(site)
        self.driver.implicitly_wait(1)

        zipcode = self.driver.find_element_by_id("covid_vaccine_search_input") 
        #zipcode = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "covid_vaccine_search_input")))
        zipcode.send_keys(self.config["zip"])
        button = self.driver.find_element_by_css_selector("#covid_vaccine_search .btn-primary")
        #button = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#covid_vaccine_search .btn-primary")))
        button.click()
        #self.driver.implicitly_wait(5)
        #print("Iterating through content")
        #content = self.driver.find_elements_by_css_selector("#covid_vaccine_store_list_content .radio-group-container .store-list-row")
        selector = "#covid_vaccine_store_list_content .radio-group-container .store-list-row"
        print("Finding store list content")
        content = WebDriverWait(self.driver, TIMEOUT).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, selector)))
        #self.driver.implicitly_wait(int(TIMEOUT) / 2)
        #content = content.find_elements_by_css_selector(".radio-group-container .store-list-row")

        print("Content length: %s " % (str(len(content))))
        for div in content:
            second = div.find_elements_by_css_selector("div")[1]
            if second.text.upper() != "NO":
                return True, site 

        return False, None

        #submit = self.driver.find_element_by_id("")

    def check_walgreens(self):
        config = self.sites["walgreens"]
        self.driver.get(config["login"])
        username = self.driver.find_element_by_name("username")
        username.send_keys(config["email"])
        password = self.driver.find_element_by_name("password")

        password.send_keys(config["password"])

        url = self.driver.current_url
        submit = self.driver.find_element_by_id("submit_btn").click()

        print(username.get_attribute("value"))
        print(password.get_attribute("value"))
        self.driver.implicitly_wait(5)
        error = self.driver.find_element_by_id("error_msg")
        print(error.get_attribute("innerHTML"))
        #WebDriverWait(self.driver, TIMEOUT).until(EC.url_changes(url))



        url = self.driver.current_url
        print(url)
        self.driver.get(config["timeslots"])


        cookies = self.driver.get_cookies()
        s = requests.Session()
        for cookie in cookies:
            s.cookies.set(cookie["name"], cookie["value"])

        """

        args = {}
        args["appointmentAvailability"] = { "startDateTime": datetime.datetime.now().strftime("%Y-%m-%d")}
        args["position"] = { "latitude": self.config["latitude"], "longitude": self.config["longitude"] }
        args["radius"] = self.config["radius"]
        args["serviceId"] = 99
        args["size"] = self.config["size"]
        args["state"] = self.config["state"]
        args["vaccine"] = { "productId": "" }
       
        print(args) 
        r = s.post(config["timeslots"], data=args)
        print(r.content)
        """

    def check_ohsu(self):
        site = self.sites["ohsu"]
        self.driver.get(site)
        div =  self.driver.find_element_by_id("EndOfSurvey")
        #print(div.get_attribute("innerHTML"))
        if div:
            return False, None
        return True, site


    def send_email(self, title, msg):
        server = smtplib.SMTP(self.config["smtp"], self.config["port"])
        server.starttls()
        server.login(self.config["email"], self.config["password"])
        for r in self.config["receivers"]:
            m = EmailMessage()

            m["Subject"] = title
            m["From"] = self.config["email"]
            m["To"] = r
            m.set_type("text/html")
            m.set_content(msg)

            server.sendmail(self.config["email"], r, m.as_string())
        server.quit()


    def close(self):
        self.driver.quit()

def main(argv):
    n = NotifyVax()
    try:
        #print(n.check_ohsu())
        #print(n.check_albertsons())
        #print(n.check_costco())
        print(n.check_walgreens())
    finally:
        n.close()


if __name__ == "__main__":
    main(sys.argv[1:])
