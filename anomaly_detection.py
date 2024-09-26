import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import get_driver
import pandas as pd
import chardet


def create_dataset():
    driver = get_driver()  # Ensure get_driver() is correctly defined in your utils
    with open("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", 'rb') as f:
        result = chardet.detect(f.read())

    # Get the encoding
    encoding = result['encoding']

    # Read the CSV with the detected encoding
    cities = pd.read_csv("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", encoding=encoding)
    for city in cities["שם_ישוב"]:
        print(city)
        driver.get("https://www.nadlan.gov.il/")

        try:
            # Wait for the search box to be present
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="SearchString"]'))
            )
            search_box.send_keys(city)
            search_box.send_keys(Keys.RETURN)

            # Wait for the search button and click
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="submitSearchBtn"]'))
            )
            search_button.click()
        except TimeoutException:
            print(f"Timed out waiting for elements on {driver.current_url}")
            continue

        time.sleep(5)  # Optional delay for loading

        # Check if still on the search page
        if driver.current_url == "https://www.nadlan.gov.il/":
            print(driver.current_url)
            print("Not found")
            try:
                # Clear the search box and retry
                search_box = driver.find_element(By.XPATH, '//*[@id="SearchString"]')
                search_box.clear()
            except NoSuchElementException:
                print("Search box not found on retry.")
            continue
        else:
            print("Found")

            try:
                # Locate the sales table by class name
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "myTable"))
                )

                # Locate all rows in the table
                rows = table.find_elements(By.CLASS_NAME, "tableRow")
                previous_number_of_rows = 0

                # Scroll and check for new rows until no more are loaded
                while True:
                    # Scroll to the bottom of the page
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for new content to load

                    # Refresh the list of rows after scrolling
                    rows = table.find_elements(By.CLASS_NAME, "tableRow")
                    number_of_rows = len(rows)

                    print(f"Rows found: {number_of_rows}")

                    # Break if no new rows are loaded
                    if number_of_rows == previous_number_of_rows:
                        break
                    previous_number_of_rows = number_of_rows

                if number_of_rows == 0:
                    print("0 records of sales found")
                    continue
                else:
                    print(f"Total rows found after scrolling: {number_of_rows}")

            except (NoSuchElementException, TimeoutException):
                print("Table or rows not found.")
                continue

    driver.quit()


if __name__ == "__main__":
    create_dataset()
