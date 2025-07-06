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
    response.raise_for_status() # Raise an exception for HTTP errors
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table data cell that contains "Spain"
    # Using 'string' instead of 'text' for more reliable matching
    spain_td = soup.find('td', string='Spain') 
    
    if not spain_td:
        print("Could not find 'Spain' table data cell.")
        return None

    # Find the parent row of the "Spain" cell
    spain_row = spain_td.find_parent('tr')
    
    if not spain_row:
        print("Could not find parent row for 'Spain' cell.")
        return None

    # Find the <span> element within this row that contains the status
    # We look for a <span> with class 'label' and then get its text.
    status_span = spain_row.find('span', class_='label') 
    
    if status_span:
        # Return the stripped text content of the span (e.g., "paused", "open")
        return status_span.get_text(strip=True)
    else:
        print("Could not find status <span> within Spain row.")
        return None # No status span found within the row

def get_current_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_previous_hash():
    if not os.path.exists(HASH_FILE):
        return None
    try:
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading previous hash: {e}")
        return None

def save_hash(hash_value):
    try:
        with open(HASH_FILE, "w") as f:
            f.write(hash_value)
    except Exception as e:
        print(f"Error saving hash: {e}")

def send_email(current_status_text):
    sender_email = os.environ.get('EMAIL_FROM')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    recipient_email = os.environ.get('EMAIL_TO')

    if not all([sender_email, sender_password, recipient_email]):
        print("Email environment variables not set. Cannot send email.")
        return

    email_body = f"Spain's Working Holiday visa status has changed!\n\nNew Status: {current_status_text}\n\nURL: {URL}"
    msg = MIMEText(email_body)
    msg['Subject'] = f"Visa Status Alert: Spain - {current_status_text}"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    content = get_spain_status()
    if content is None:
        print("Could not retrieve Spain's status content. Exiting.")
        return

    current_hash = get_current_hash(content)
    previous_hash = load_previous_hash()

    if current_hash != previous_hash:
        print(f"Change detected! New status: {content}")
        send_email(content)
        save_hash(current_hash)
    else:
        print(f"No change. Current status: {content}")

if __name__ == "__main__":
    main()
