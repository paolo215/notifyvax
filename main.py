
import requests
import config
import smtplib
import ssl
import sys
import email
import bs4
import datetime
import json
import time
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from email.message import EmailMessage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

"""
#Safeway and Albertsons
#Costco
#Walgreens (or 1-800-WALGREENS) 
Walmart
Bi-Mart
#Rite Aid
#CVS
Fred Meyer
"""

TIMEOUT = 30

class NotifyVax:

    def __init__(self):
        self.config = config.config
        self.sites = self.config["sites"]

        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        #options.add_argument("enable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        options.add_argument("disable-features=NetworkService")
        options.page_load_strategy = "normal"
        self.os_name = os.name
        if self.os_name == "nt":
            self.driver = webdriver.Chrome("./driver/chromedriver.exe", chrome_options=options)
        elif self.os_name == "posix":
            options.add_argument("--headless")
            self.driver = webdriver.Chrome("./driver/chromedriver", chrome_options=options)
        

    def scan(self):

        title = "COVID Vaccine Scheduling"
        found = False
        messages = []
        try:
            ohsu = self.check_ohsu()
            if ohsu:
                messages.append("OHSU vaccination scheduling may be available: " + ohsu)
                found = True
        except Exception as e:
            print("OHSU scan error occurred")
            print(e)

        try:
            albertsons = self.check_albertsons()
            if albertsons:
                messages.append("Albertsons scheduling may be available: " + albertsons)
                found = True
        except Exception as e:
            print("Albertsons scan error occurred")
            print(e)

        try:
            costco = self.check_costco()
            if costco:
                messages.append("Costco scheduling may be available: " + costco)
                found = True
        except Exception as e:
            print("Costco scan error occurred")
            print(e)

        try:
            if self.os_name == "nt":
                walgreens = self.check_walgreens()
                if walgreens:
                    messages.append("Walgreens scheduling may be available: " + walgreens)
                    found = True
        except Exception as e:
            print("Walgreens scan error occurred")
            print(e)

        try:
            cvs = self.check_cvs()
            if cvs:
                messages.append("CVS scheduling may be available: " + cvs)
                found = True
        except Exception as e:
            print("CVS scan error occurred")
            print(e)

        try:
            riteaid = self.check_riteaid()
            if riteaid:
                messages.append("RiteAid scheduling may be available: " + riteaid)
                found = True
        except Exception as e:
            print("RiteAid scan error occurred")
            print(e)

            
        if found:
            print("Found available covid vaccination scheduling site")
            print(messages)
            self.send_email(title, "\r\n".join(messages))
        #else:
        #    print("No available covid vaccination scheduling found")
        #    self.send_email(title, "No available covid vaccination scheduling found")

    def check_costco(self):
        for s in self.sites["costco"]:
            self.driver.get(s)
            self.driver.implicitly_wait(1)

            try:
                body = self.driver.find_element_by_tag_name("body")
                body_text = body.text
                if "scheduling is not currently available" in body_text \
                   or "site is temporarily disabled" in body_text:
                    return None
                else:
                    return s
            except NoSuchElementException:
                print("Body not found")
            
        return None

    def check_albertsons(self):
        site = self.sites["albertsons"]
        self.driver.get(site)
        self.driver.implicitly_wait(3)

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
                return site 

        return None

        #submit = self.driver.find_element_by_id("")

    def login_walgreens(self):
        url = self.driver.current_url
        config = self.sites["walgreens"]
        if ".com/login" in url:
            username = self.driver.find_element_by_name("username")
            username.send_keys(config["email"])
            password = self.driver.find_element_by_name("password")

            password.send_keys(config["password"])

            url = self.driver.current_url
            self.driver.find_element_by_id("submit_btn").click()
            self.driver.implicitly_wait(5)
            try:
                error = self.driver.find_element_by_id("error_msg")
                print(error.get_attribute("innerHTML"))
            except NoSuchElementException:
                print("No error_msg element found")

            url = self.driver.current_url
            if "verify_identity" in url:
                radio_email = self.driver.find_element_by_id("radio-security")
                radio_email.click()
                self.driver.find_element_by_id("optionContinue").click()
                self.driver.implicitly_wait(2)
                answer = self.driver.find_element_by_name("SecurityAnswer")
                answer.send_keys(config["securityAnswer"])
                self.driver.find_element_by_id("validate_security_answer").click()     

    def check_walgreens(self):
        config = self.sites["walgreens"]
        self.driver.get(config["login"])
        self.login_walgreens()
        

        self.driver.implicitly_wait(5)
        url = self.driver.current_url
        if "/appointment/patient-info" in url:
            self.driver.find_element_by_id("continueBtn").click()

        url = self.driver.current_url
        if "/covid-19/location-screening" in url:
            input_location = self.driver.find_element_by_id("inputLocation")
            input_location.clear()
            input_location.send_keys(self.config["zip"])
            self.driver.implicitly_wait(2)
            self.driver.find_element_by_css_selector("section .LocationSearch_container .btn").click()
            self.driver.implicitly_wait(2)
            error = None
            try:
                error = self.driver.find_element_by_css_selector(".alert__red")
                #if error:
                 #   return False
            except NoSuchElementException:
                print("No alert found")

            #available = self.driver.find_element_by_css_selector(".alert__green")
            #if available:
            #    return True
        self.driver.get(config["nextAvailable"])
        self.driver.implicitly_wait(3)
        url = self.driver.current_url
        """
        if "/appointment/next-available" in url:
            input_location = self.driver.find_element_by_id("inputLocation")
            input_location.clear()
            input_location.send_keys(self.config["zip"])
            self.driver.find_element_by_css_selector("#icon__search").click()
        """ 

        #self.driver.find_element_by_css_selector("#icon_search").click()                
        #WebDriverWait(self.driver, TIMEOUT).until(EC.url_changes(url))
        url = self.driver.current_url
        #self.driver.get(config["timeslots"])


        s = self.get_cookies()
        
        header = {}
        header["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        header["content-type"] = "application/json; charset=UTF-8"
        header["accept"] = "application/json, text/plain, */*"
        args = {}
        args["appointmentAvailability"] = { "startDateTime": datetime.datetime.now().strftime("%Y-%m-%d")}
        args["position"] = { "latitude": self.config["latitude"], "longitude": self.config["longitude"] }
        args["radius"] = self.config["radius"]
        args["serviceId"] = "99"
        args["size"] = self.config["size"]
        args["state"] = self.config["state"]
        args["vaccine"] = { "productId": "" }
        args = json.dumps(args, separators=(",", ":"))
        
        
        print(args) 
        r = s.post(config["timeslots"], headers=header, data=args)
        response = r.json()
        print(response)
        if "error" in response or "errors" in response:
            return None
        return config["nextAvailable"]

    def check_cvs(self):
        config = self.sites["cvs"]
        site = config["covidSite"]

        self.driver.get(site)
        s = self.get_cookies()
        self.driver.implicitly_wait(3)

        header = {}
        header["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        header["content-type"] = "application/json;charset=iso-8859-1"
        header["accept"] = "application/json, text/plain, */*"
        header["Referer"] = "https://www.cvs.com/immunizations/covid-19-vaccine"

        r = s.get(config["covidInfo"], headers=header)
        response = r.json()
        state_data = response["responsePayloadData"]["data"][self.config["state"]]
        for data in state_data:
            if data["status"] != "Fully Booked":
                return site
        return None
            
    def check_riteaid(self):
        config = self.sites["riteAid"]
        header = {}
        header["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        header["content-type"] = "application/json;charset=iso-8859-1"
        header["accept"] = "application/json, text/plain, */*"
        header["Referer"] = "https://www.riteaid.com/pharmacy/apt-scheduler"

        self.driver.get(config["covidSite"])
        s = self.get_cookies()
        self.driver.implicitly_wait(3)
        
        for site in config["sites"]:
            r = s.get(site, headers=header)
            response = r.json()
            slots = response["Data"]["slots"]
            print(site, slots)
            for slot in slots:
                if slot == True:
                    return config["covidSite"]
        return None
        

    def check_ohsu(self):
        site = self.sites["ohsu"]
        self.driver.get(site)
        self.driver.implicitly_wait(3) 
        div = None
        try:
            div =  self.driver.find_element_by_id("EndOfSurvey")
            #print(div.get_attribute("innerHTML"))
        except NoSuchElementException:
            print("Cannot find EndOfSurvey... Questinnaires may be available")
        if div:
            return None
        return site

    def get_cookies(self):
        cookies = self.driver.get_cookies()
        s = requests.Session()
        for cookie in cookies:
            s.cookies.set(cookie["name"], cookie["value"])
        return s

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
    try:
        n = NotifyVax()
        while True:
            n.scan()
            #n.check_walgreens()
            print("Scan done")
            time.sleep(60*10)
            

    finally:
        n.close()


if __name__ == "__main__":
    main(sys.argv[1:])
