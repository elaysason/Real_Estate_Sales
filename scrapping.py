import os
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import smtplib
from selenium.webdriver.chrome.options import Options
import sys
import json


def search_website(search_place):
    # Set up Chrome in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(
        "https://www.nadlan.gov.il/")

    # Perform search
    search_box = driver.find_element(By.XPATH,
                                     '//*[@id="SearchString"]')
    search_box.send_keys(search_place)  # Replace "Your search query here" with your actual search query
    search_box.send_keys(Keys.RETURN)

    search_button = driver.find_element(By.XPATH,
                                        '//*[@id="submitSearchBtn"]')
    search_button.click()

    time.sleep(25)

    latest_sale = [driver.find_element(By.XPATH,
                                       "/html/body/div[2]/div[2]/div[2]/div[1]/div[3]/div/grid-directive/div/div[1]/button/div[" + str(
                                           1 + i) + "]/div").accessible_name for i in range(8)]
    latest_date = datetime.strptime(latest_sale[0], "%d.%m.%Y")

    new_sale = False
    # selector for your search box
    cur_latest_date_string = "latest_sale.txt"
    if not os.path.exists(cur_latest_date_string):

        # Write a message if the file doesn't exist
        new_sale = True
        with open(cur_latest_date_string, "w") as f:
            f.write(latest_sale[0])
    else:

        with open(cur_latest_date_string, 'r') as f:
            cur_latest = datetime.strptime(f.read(), "%d.%m.%Y")
            if cur_latest < latest_date:
                new_sale = True

    if new_sale:
        with open(cur_latest_date_string, "w") as f:
            f.write(latest_sale[0])

    url = driver.current_url
    # Close the browser
    driver.quit()
    return new_sale, latest_sale, url


def sale_email(sale_details, sale_url, sender_email, receiver_emails, password):
    # Email configuration
    sender_email = sender_email
    receiver_emails = receiver_emails
    password = password  # Replace with your email password
    subject = "דירה חדשה נמכרה!"
    for receiver_email in receiver_emails:
        # Set up the email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        body = f"בתאריך {sale_details[0]} נמכרה {sale_details[3]} בכתובת {sale_details[1]} עם {sale_details[4]} חדרים בקומה {sale_details[5]} בשטח {sale_details[6]} ובמחיר {sale_details[7]} .שקל " + "\n לעוד פרטים ולאתר: " + str(
            sale_url)
        # Set up the email message
        message = MIMEMultipart("related")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        html_content = f"""
        <html>
        <head>
            <style>
                p {{
                    direction: rtl;
                    text-align: right;
                }}
            </style>
        </head>
        <body>
            <p>{body}</p>
        </body>
        </html>
        """

        # Attach HTML content to the email
        message.attach(MIMEText(html_content, "html"))

        # Connect to the email server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())

        # Closing the connection
        server.quit()


def validate_parameters(args):
    if len(args) != 2:
        raise ValueError("Usage: scrapping.py <config_file_path>")


def load_config(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"The configuration file {json_path} does not exist.")

    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    try:
        validate_parameters(sys.argv)
        config_file_path = load_config(sys.argv[1])

        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        desired_location = config['desired_location']
        sender_email = config['sender_email']
        receiver_emails = config['receiver_emails']
        email_password = config['email_password']

        new_sale, latest_sale, latest_url = search_website(desired_location)

        if new_sale:
            sale_email(latest_sale, latest_url, sender_email, receiver_emails, email_password)
            print('Finished the run, new sale recorded and email sent.')
        else:
            print('Finished the run, no new sale')

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
