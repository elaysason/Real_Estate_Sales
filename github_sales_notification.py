import json
import smtplib
import sys
import time
import os
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from time import sleep
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils import validate_parameters, validate_config, get_driver

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sales_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def search_website(search_place):
    logging.info(f"Starting website search for place: {search_place}")

    driver = get_driver("https://dev.nadlan.gov.il/")
    logging.info("Webdriver launched and navigating to site.")
    logging.info("Current URL: {driver.current_url}")

    try:
        logging.debug("Waiting for the search input to become visible...")
        WebDriverWait(driver, 600).until(
            EC.visibility_of_element_located((By.ID, "myInput2"))
        )
        logging.info("Search input is visible.")

        # Enter the search term
        search_box = driver.find_element(By.ID, "myInput2")
        search_box.send_keys(search_place)
        logging.info("Search term entered.")

        wait = WebDriverWait(driver, 600)
        top_suggestion = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "ul.react-autosuggest__suggestions-list > li.react-autosuggest__suggestion")
        ))
        top_suggestion.click()
        logging.info("Top suggestion selected.")

        WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr.mainTable__row"))
        )
        logging.info("Sales table loaded.")

        rows = driver.find_elements(By.CSS_SELECTOR, "table#dealsTable tbody > tr.mainTable__row")
        cells = rows[0].find_elements(By.TAG_NAME, "td")
        latest_sale = [cell.text.strip() for cell in cells]
        logging.debug(f"Extracted latest sale data: {latest_sale}")

        latest_date = datetime.strptime(latest_sale[3], "%d/%m/%Y")
        new_sale = False
        file_path = "latest_sale.txt"

        if not os.path.exists(file_path):
            logging.info("No previous record found. Treating as first run.")
            new_sale = True
            with open(file_path, "w") as f:
                f.write(latest_sale[3])
        else:
            with open(file_path, 'r') as f:
                previous_date = datetime.strptime(f.read().strip(), "%d/%m/%Y")
                if latest_date > previous_date:
                    logging.info(f"New sale detected: {latest_date} > {previous_date}")
                    new_sale = True
                else:
                    logging.info("No new sale found.")

        if new_sale:
            with open(file_path, "w") as f:
                f.write(latest_sale[3])
                logging.debug("Updated latest_sale.txt with new date.")

        url = driver.current_url
        logging.info("Search process complete.")
        return new_sale, latest_sale, url

    except Exception as e:
        logging.exception("Error occurred during scraping process.")
        raise

    finally:
        driver.quit()
        logging.info("Browser session closed.")


def take_govmap_screenshot(address, output_path="govmap_screenshot.png"):
    try:
        query = quote_plus(address)
        logging.info(f"Generating GovMap screenshot for: {address}")
        driver = get_driver(f"https://www.govmap.gov.il/?q={query}")
        time.sleep(8)
        driver.save_screenshot(output_path)
        logging.info(f"Screenshot saved at: {output_path}")
    except Exception as e:
        logging.exception("Failed to take GovMap screenshot.")
        raise
    finally:
        driver.quit()
        logging.info("GovMap browser session closed.")

def take_city_renewal_screenshot(address, output_path = "city_renewal_screenshot.png"):
    try:
        logging.info("Generating CityRenewal screenshot for: {address}")
        driver = get_driver("https://moch.maps.arcgis.com/apps/webappviewer/index.html?id=d6191754d18a4fd29ee2e2ca1d040759")
        logging.info("Webdriver launched and navigating to מפת התחדשות עירונית")
        WebDriverWait(driver, 600).until(
            EC.visibility_of_element_located((By.ID, "widgets_Search_Widget_3"))
        )
        search_box = driver.find_element(By.ID, "widgets_Search_Widget_3")
        search_box.send_keys(address)
        logging.info("Search term entered.")
        zoom_out_button = driver.find_element(By.CLASS_NAME, "zoom-out")
        zoom_out_button.click()
        time.sleep(0.5)
        zoom_out_button.click()


    except Exception as e:
        logging.exception("Failed to take CityRenewal screenshot.")
        raise
    finally:
        driver.quit()
        logging.info("CityRenewal browser session closed.")



def sale_email(sale_details, sale_url, sender_email, receiver_emails, password):
    subject = "דירה חדשה נמכרה!"
    address = sale_details[1]

    logging.info(f"Preparing to send email alert for sale at: {address}")
    take_govmap_screenshot(address)

    encoded_address = quote_plus(address)
    govmap_url = f"https://www.govmap.gov.il/?q={encoded_address}"
    map_image_path = "govmap_screenshot.png"

    for receiver_email in receiver_emails:
        try:
            message = MIMEMultipart("related")
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject

            html = f"""
            <html>
              <body dir="rtl" style="direction: rtl;">
                <p>שלום,</p>
                <p>בתאריך <strong>{sale_details[3]}</strong> נמכרה <strong>{sale_details[6]}</strong><br>
                   בכתובת <strong>{address}</strong> עם <strong>{sale_details[7]}</strong> חדרים<br>
                   בקומה <strong>{sale_details[8]}</strong>, בשטח של <strong>{sale_details[2]}</strong> מ"ר,<br>
                   ובמחיר של <strong>{sale_details[4]}</strong>.
                </p>
                <p>
                  🔗 <a href="{sale_url}">פרטי העסקה</a><br>
                  🗺️ <a href="{govmap_url}">צפה במפה (GovMap)</a>
                </p>
                <img src="cid:govmapimage" width="600" />
              </body>
            </html>
            """
            message.attach(MIMEText(html, "html"))

            if os.path.exists(map_image_path):
                with open(map_image_path, 'rb') as img:
                    mime_img = MIMEImage(img.read(), _subtype='png')
                    mime_img.add_header('Content-ID', '<govmapimage>')
                    mime_img.add_header('Content-Disposition', 'inline', filename="govmap.png")
                    message.attach(mime_img)
                logging.debug("Map image attached to email.")
            else:
                logging.warning("Map image not found. Skipping image attachment.")

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                logging.info(f"Email sent successfully to: {receiver_email}")
        except Exception as e:
            logging.exception(f"Failed to send email to: {receiver_email}")


def load_config(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"The configuration file {json_path} does not exist.")
    with open(json_path, 'r', encoding='utf-8') as f:
        config_loaded = json.load(f)
        validate_config(config_loaded)
        return config_loaded


if __name__ == "__main__":
    logging.info("=== Starting new monitoring cycle ===")
    try:
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
        logging.info("Environment configuration loaded and validated.")

        new_sale, latest_sale, latest_url = search_website(desired_location)

        if new_sale:
            logging.info("New sale detected! Sending email...")
            sale_email(latest_sale, latest_url, email_username, email_list, email_password)
            logging.info("Run complete. Notification sent.")
        else:
            logging.info("Run complete. No new sales detected.")

    except Exception as e:
        logging.exception("Fatal error occurred during run.")
        sys.exit(1)
