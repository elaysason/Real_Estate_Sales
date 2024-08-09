import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from utils import get_driver
import pandas as pd
import chardet


def create_dataset():
    driver = get_driver()
    with open("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", 'rb') as f:
        result = chardet.detect(f.read())

    # Get the encoding
    encoding = result['encoding']

    # Read the CSV with the detected encoding
    cities = pd.read_csv("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", encoding=encoding)
    for city in cities["שם_ישוב"]:
        print(city)

        # Perform search
        search_box = driver.find_element(By.XPATH,
                                         '//*[@id="SearchString"]')

        time.sleep(10)
        search_box.clear()

        search_box.send_keys(city)
        search_box.send_keys(Keys.RETURN)

        search_button = driver.find_element(By.XPATH,
                                            '//*[@id="submitSearchBtn"]')
        search_button.click()
        try:
            error_button = driver.find_element(By.XPATH,
                                               '/html/body/div[2]/div/div[1]/div[1]/div/div[2]/search-control-directive/div/div')
            continue
        except Exception as e:
            table = driver.find_element(By.XPATH,
                                        '/html/body/div[2]/div[2]/div[2]/')  # Replace with the actual XPath or locator for your table

            # Locate all rows in the table
            rows = table.find_elements(By.TAG_NAME, "tr")

            # Get the number of rows
            number_of_rows = len(rows)

            # Loop through the rows
            print(number_of_rows)
            driver.get(
                "https://www.nadlan.gov.il/")

if __name__ == "__main__":
    create_dataset()
