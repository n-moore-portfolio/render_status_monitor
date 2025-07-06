import requests
from bs4 import BeautifulSoup
import hashlib
import smtplib
from email.mime.text import MIMEText
import os

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"
HASH_FILE = "last_hash.txt"

def get_spain_status():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    spain_row = soup.find('td', text='Spain')
    if not spain_row:
        return None

    tr = spain_row.find_parent('tr')
    return str(tr)

def get_current_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_previous_hash():
    if not os.path.exists(HASH_FILE):
        return None
    with open(HASH_FILE, "r") as f:
        return f.read().strip()

def save_hash(hash_value):
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)

def send_email():
    msg = MIMEText("Spain's Working Holiday visa status has changed!\n\n" + URL)
    msg['Subject'] = "Visa Status Alert: Spain"
    msg['From'] = os.environ['EMAIL_FROM']
    msg['To'] = os.environ['EMAIL_TO']

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(os.environ['EMAIL_FROM'], os.environ['EMAIL_PASSWORD'])
    server.send_message(msg)
    server.quit()

def main():
    content = get_spain_status()
    if content is None:
        print("Could not find Spain row.")
        return

    current_hash = get_current_hash(content)
    previous_hash = load_previous_hash()

    if current_hash != previous_hash:
        print("Change detected!")
        send_email()
        save_hash(current_hash)
    else:
        print("No change.")

if __name__ == "__main__":
    main()
