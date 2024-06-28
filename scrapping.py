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
from geopy.geocoders import Photon


def search_website():
    # Set up Chrome in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(
        "https://www.nadlan.gov.il/")  # Replace "https://example.com" with the URL of the website you want to search

    # Perform search
    search_box = driver.find_element(By.XPATH,
                                     '//*[@id="SearchString"]')  # Replace "input.search-board" with the correct CSS selector for your search box
    search_box.send_keys("כפר גנים ג")  # Replace "Your search query here" with your actual search query
    search_box.send_keys(Keys.RETURN)

    search_button = driver.find_element(By.XPATH,
                                        '//*[@id="submitSearchBtn"]')
    search_button.click()

    time.sleep(5)
    time.sleep(20)

    latest_sale = [driver.find_element(By.XPATH,
                                      "/html/body/div[2]/div[2]/div[2]/div[1]/div[3]/div/grid-directive/div/div[1]/button/div["+str(1+i)+"]/div").accessible_name for i in range(8)]
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
    url = driver.current_url
    # Close the browser
    driver.quit()
    return new_sale, latest_sale,url

def send_email1(sale_details,url):
    # Email configuration
    sender_email = "elaysason123@gmail.com"
    receiver_emails = ["moshesason100@gmail.com","sasonsarit1@gmail.com"]
    password = "gqzd arfn gpmc yrxu"  # Replace with your email password
    subject = "דירה חדשה נמכרה!"
    for receiver_email in receiver_emails:
        # Set up the email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Create HTML content for the email
        body = f"בתאריך {sale_details[0]} נמכרה {sale_details[3]} בכתובת {sale_details[1]} עם {sale_details[4]} חדרים בקומה {sale_details[5]} בשטח {sale_details[6]} ובמחיר {sale_details[7]} .שקל " + "\n לעוד פרטים ולאתר: "+str(url)

        # Set up the email message
        message = MIMEMultipart("related")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # Create HTML content for the email with right-to-left direction
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

        # Connect to the SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)  # Replace "smtp.example.com" with your SMTP server and port
        server.starttls()
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())

        # Close the connection
        server.quit()

if __name__ == "__main__":

    # Initialize a geocoder
#   geolocator = Photon(user_agent="geoapiExercises")

#   # Street address you want to convert to coordinates
#   street_address = "12 Meissner St, Petah Tikva, Israel"

#   # Use the geocoder to get the latitude and longitude
#   location = geolocator.geocode(street_address)
#   print("input ", street_address)
#   if location:
#       latitude = location.latitude
#       longitude = location.longitude
#       print("Latitude:", latitude)
#       print("Longitude:", longitude)
#   else:
#       print("Address not found.")
    new_sale, latest_sale,url = search_website()

    if new_sale:
        send_email1(latest_sale,url)
        print('Finished the run, new sale recorded and email sent.')
    print('Finished the run, no new sale')
