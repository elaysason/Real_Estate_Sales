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
        driver.get(
            "https://www.nadlan.gov.il/")

        # Perform search
        search_box = driver.find_element(By.XPATH,
                                         '//*[@id="SearchString"]')

        time.sleep(20)

        search_box.send_keys(city)
        search_box.send_keys(Keys.RETURN)

        search_button = driver.find_element(By.XPATH,
                                            '//*[@id="submitSearchBtn"]')
        search_button.click()
        time.sleep(20)

        if driver.current_url == "https://www.nadlan.gov.il/":
            print(driver.current_url)
            print("Not found")
            search_box = driver.find_element(By.XPATH, '//*[@id="SearchString"]')
            time.sleep(10)
            search_box.clear()

            continue
        else:
            print("Found")

            table = driver.find_element(By.CLASS_NAME, "myTable")


            # Locate all rows in the table
            rows = table.find_elements(By.CLASS_NAME, "tableRow")

            # Get the number of rows
            number_of_rows = len(rows)
            if number_of_rows == 0:
                print("0 records of sales found")
                continue
            # Loop through the rows
            print(number_of_rows)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


if __name__ == "__main__":
    create_dataset()
