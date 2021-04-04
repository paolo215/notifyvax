
import requests
import config
import smtplib
import ssl
import sys
import email

from email.message import EmailMessage

class NotifyVax:

    def __init__(self):
        self.config = config.config
        

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

def main(argv):
    n = NotifyVax()


if __name__ == "__main__":
    main(sys.argv[1:])
