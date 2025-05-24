import json
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from urllib.parse import quote_plus
from email.mime.image import MIMEImage
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils import validate_parameters, validate_config, get_driver


def search_website(search_place):
    """
    Set up Chrome in headless mode, perform a search using the given search_place,
    check for new sales, and return the new_sale flag, latest_sale list, and the current URL.

    :param search_place: The place to search for sales.
    :return: A tuple containing new_sale flag (bool), latest_sale list, and the current URL.
    """

    # Set up Chrome in headless mode
    driver = get_driver("https://dev.nadlan.gov.il/")

    # Wait for the page to load
    time.sleep(10)

    # Perform search
    search_box = driver.find_element(By.ID, "myInput2")
    search_box.send_keys(search_place)

    # Wait until the suggestion list appears
    wait = WebDriverWait(driver, 10)
    top_suggestion = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "ul.react-autosuggest__suggestions-list > li.react-autosuggest__suggestion")
    ))

    # Click the top suggestion
    top_suggestion.click()
   # select_element = driver.find_elements(By.ID,"react-autowhatever-1--item-0")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tr.mainTable__row"))
    )
    first_row = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "table#dealsTable tbody > tr.mainTable__row")
    ))
    rows = driver.find_elements(By.CSS_SELECTOR, "table#dealsTable tbody > tr.mainTable__row")
    cells = rows[0].find_elements(By.TAG_NAME, "td")
    print(cells)

    latest_sale =  [cell.text.strip() for cell in cells]
    print(latest_sale)

    # latest_sale = [option.text for option in select_element]
   # print(latest_sale)
    latest_date = datetime.strptime(latest_sale[3], "%d/%m/%Y")
    # Flag for checking if there is a new sale

    new_sale = False
    cur_latest_date_string = "latest_sale.txt"
    if not os.path.exists(cur_latest_date_string):
        new_sale = True
        with open(cur_latest_date_string, "w") as f:
            f.write(latest_sale[0])
    else:

        with open(cur_latest_date_string, 'r') as f:
            cur_latest = datetime.strptime(latest_sale[3], "%d/%m/%Y")
            if cur_latest < latest_date:
                new_sale = True

    if new_sale:
        with open(cur_latest_date_string, "w") as f:
            f.write(latest_sale[3])

    url = driver.current_url
    # Close the browser
    driver.quit()
    return new_sale, latest_sale, url


def take_govmap_screenshot(address, output_path="govmap_screenshot.png"):
    query = quote_plus(address)
    driver = get_driver(f"https://www.govmap.gov.il/?q={query}")
    time.sleep(8)  # Wait for the map to load
    driver.save_screenshot(output_path)
    driver.quit()

def sale_email(sale_details, sale_url, sender_email, receiver_emails, password):
    subject = "דירה חדשה נמכרה!"
    address = sale_details[1]
    take_govmap_screenshot(address)

    encoded_address = quote_plus(address)
    govmap_url = f"https://www.govmap.gov.il/?q={encoded_address}"

    map_image_path = "govmap_screenshot.png"  # <-- must be created before calling this function

    for receiver_email in receiver_emails:
        message = MIMEMultipart("related")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        # HTML email content
        html = f"""
        <html>
          <head>
            <meta charset="UTF-8">
          </head>
          <body dir="rtl" style="direction: rtl; text-align: right; font-family: Arial, sans-serif;">
            <div style="padding: 20px;">
              <p style="direction: rtl; text-align: right;">שלום,</p>
              <p style="direction: rtl; text-align: right;">
                בתאריך <strong>{sale_details[3]}</strong> נמכרה <strong>{sale_details[6]}</strong><br>
                בכתובת <strong>{address}</strong> עם <strong>{sale_details[7]}</strong> חדרים<br>
                בקומה <strong>{sale_details[8]}</strong>, בשטח של <strong>{sale_details[2]}</strong> מ"ר,<br>
                ובמחיר של <strong>{sale_details[4]}</strong>.
              </p>
              <p style="direction: rtl; text-align: right;">
                🔗 <a href="{sale_url}" target="_blank">פרטי העסקה</a><br>
                🗺️ <a href="{govmap_url}" target="_blank">צפה במפה הממשלתית (GovMap)</a>
              </p>
              <a href="{govmap_url}" target="_blank">
                <img src="cid:govmapimage" width="600" style="border:1px solid #ccc;" />
              </a>
              <p style="direction: rtl; text-align: right;">בברכה,<br>המערכת</p>
            </div>
          </body>
        </html>
        """

        message.attach(MIMEText(html, "html"))

        # Embed the image
        if os.path.exists(map_image_path):
            with open(map_image_path, 'rb') as img:
                mime_img = MIMEImage(img.read(), _subtype='png')
                mime_img.add_header('Content-ID', '<govmapimage>')
                mime_img.add_header('Content-Disposition', 'inline', filename="govmap.png")
                message.attach(mime_img)
        else:
            print("Warning: govmap_screenshot.png not found. Skipping image attachment.")

        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())


def load_config(json_path):
    """
    Load a configuration file from the specified JSON path and validate its contents.

    Args:
        json_path (str): The path to the JSON configuration file.

    Raises:
        FileNotFoundError: If the configuration file does not exist.

    Returns:
        dict: The loaded configuration as a dictionary.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"The configuration file {json_path} does not exist.")

    with open(json_path, 'r', encoding='utf-8') as f:
        config_loaded = json.load(f)
        validate_config(config_loaded)  # Validate the loaded configuration
        return config_loaded


if __name__ == "__main__":
    try:
        # validate_parameters(sys.argv)
        email_username = os.getenv("EMAIL_USERNAME")
        email_password = os.getenv("EMAIL_PASSWORD")
        desired_location = os.getenv("DESIRED_LOCATION")
        receiver_emails = os.getenv("RECEIVER_EMAILS", "")

        email_list = [email.strip() for email in receiver_emails.split(",") if email.strip()]
        config_from_env = {
            'desired_location': desired_location,
            'sender_email': email_username,
            'receiver_emails': email_list,
            'email_password': email_password,
        }
        validate_config(config_from_env)

        new_sale, latest_sale, latest_url = search_website(desired_location)

        if new_sale:

            sale_email(latest_sale, latest_url, email_username, email_list, email_password)
            print('Finished the run, new sale recorded and email sent.')
        else:
            print('Finished the run, no new sale')

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
