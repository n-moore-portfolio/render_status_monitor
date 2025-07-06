import requests
from bs4 import BeautifulSoup
import hashlib
import smtplib
from email.mime.text import MIMEText
import os
import unicodedata 

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"
HASH_FILE = "last_hash.txt"

def get_spain_status():
    response = requests.get(URL)
    response.raise_for_status() # Raise an exception for HTTP errors
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table data cell that contains "Spain"
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
    status_span = spain_row.find('span', class_='label') 
    
    if status_span:
        status_text = status_span.get_text(strip=True)
        
        # --- Aggressive Text Cleaning ---
        status_text = unicodedata.normalize("NFKC", status_text)
        status_text = status_text.replace('\u200b', '') 
        status_text = " ".join(status_text.split()) 
        # --- End Aggressive Text Cleaning ---

        print(f"Extracted and cleaned status text: '{status_text}' (repr: {repr(status_text)})")
        return status_text
    else:
        print("Could not find status <span> within Spain row.")
        return None

def get_current_hash(content):
    current_hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()
    print(f"Calculated current hash: '{current_hash_value}'")
    return current_hash_value

def load_previous_hash():
    if not os.path.exists(HASH_FILE):
        print(f"Hash file '{HASH_FILE}' does not exist. Returning None.")
        return None
    try:
        with open(HASH_FILE, "r") as f:
            prev_hash = f.read().strip()
            print(f"Loaded previous hash: '{prev_hash}'")
            return prev_hash
    except Exception as e:
        print(f"Error loading previous hash from '{HASH_FILE}': {e}")
        return None

def save_hash(hash_value):
    try:
        with open(HASH_FILE, "w") as f:
            f.write(hash_value)
            print(f"Saved current hash '{hash_value}' to '{HASH_FILE}'.")
    except Exception as e:
        print(f"Error saving hash to '{HASH_FILE}': {e}")

def send_email(current_status_text):
    sender_email = os.environ.get('EMAIL_FROM')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    recipient_email = os.environ.get('EMAIL_TO')

    if not all([sender_email, sender_password, recipient_email]):
        print("Email environment variables (EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO) not set. Cannot send email.")
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
    print("--- Starting Spain Visa Status Monitor ---")
    content = get_spain_status()
    if content is None:
        print("Could not retrieve Spain's status content. Exiting.")
        return

    current_hash = get_current_hash(content)
    previous_hash = load_previous_hash()

    if previous_hash is None:
        # This is the first run or the file was deleted.
        # Save the current hash but DO NOT send an email.
        print("Previous hash file not found. Initializing with current status.")
        save_hash(current_hash)
        print("Initialized hash file. No change detected for the first run.")
    elif current_hash != previous_hash:
        print(f"Change detected! Previous hash: '{previous_hash}', Current hash: '{current_hash}'")
        print(f"New status: '{content}'")
        send_email(content)
        save_hash(current_hash)
    else:
        print(f"No change. Hash: '{current_hash}'. Current status: '{content}'")
    print("--- Monitor Run Complete ---")

if __name__ == "__main__":
    main()
