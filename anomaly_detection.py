import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import get_driver
import pandas as pd
import chardet



def restart_driver(driver):
    print("Restarting driver to maintain connection...")
    driver.quit()
    time.sleep(2)  # Small delay to ensure proper shutdown
    return get_driver()

def column_value_index(driver,column_index, row_index):
    """
    Extracts the value of a specific cell based on its column and row indices.
    :param column_index: The column index of the cell (integer).
    :param row_index: The row index of the cell (integer).
    :return: Text content of the cell.
    """
    try:
        # Construct the XPath with properly formatted indices
        xpath = f'/html/body/div[2]/div[2]/div[2]/div[1]/div[3]/div/grid-directive/div/div[{row_index}]/button/div[{column_index}]'
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip()  # Strip whitespace for clean text
    except NoSuchElementException:
        print(f"Element not found for XPath: {xpath}")
        return "N/A"
    except Exception as e:
        print(f"Error in locating element: {e}")
        return "N/A"

def create_dataset():
    # Initialize driver
      # Ensure get_driver() is correctly defined in your utils

    # Detect encoding and read the city list
    with open("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    cities = pd.read_csv("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", encoding=encoding)

    # Initialize an empty list to store scraped data
    data = []
    driver = get_driver()

    restart_threshold = 10  # Set the number of iterations before restarting
    iteration_count = 0
    # Loop through each city
    for city in cities["שם_ישוב"]:
        if iteration_count % restart_threshold == 0 and iteration_count != 0:
            driver = restart_driver(driver)
        print(f"Searching for city: {city}")
        driver.get("https://www.nadlan.gov.il/")

        try:
            # Wait for the search box and enter the city name
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="SearchString"]'))
            )
            search_box.send_keys(city)
            search_box.send_keys(Keys.RETURN)

            # Wait for the search button and click it
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="submitSearchBtn"]'))
            )
            search_button.click()
        except TimeoutException:
            print(f"Timed out waiting for elements on {driver.current_url}")
            continue

        # Optional delay to allow for page to load
        time.sleep(5)

        # Check if still on the search page
        if driver.current_url == "https://www.nadlan.gov.il/":
            print("Not found, retrying...")
            try:
                search_box = driver.find_element(By.XPATH, '//*[@id="SearchString"]')
                search_box.clear()
            except NoSuchElementException:
                print("Search box not found on retry.")
            continue
        else:
            print("Data found, loading results...")
            columns = ['עיר'] + [driver.find_element(By.XPATH,
                                                     '/html/body/div[2]/div[2]/div[2]/div[1]/div[2]/div[5]/button[' + str(
                                                         i) + ']').text for i in
                                 list(range(1, 10))]  # Adjust column names based on actual data structure

            try:
                # Locate the sales table
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "myTable"))
                )

                # Start scrolling to load all data
                previous_number_of_rows = 0
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for the new rows to load
                    rows = table.find_elements(By.CLASS_NAME, "tableRow")
                    number_of_rows = len(rows)
                    print(f"Rows found: {number_of_rows}")

                    # Break if no new rows are loaded
                    if number_of_rows == previous_number_of_rows:
                        break
                    previous_number_of_rows = number_of_rows

                # Extract data from the rows if found
                if number_of_rows == 0:
                    print("0 records of sales found")
                    continue
                else:
                    print(f"Total rows found after scrolling: {number_of_rows}")
                    column_indexs = list(range(1,10))
                    # Extract data from each row
                    try:
                        # Use enumerate with map to extract data for each row and column
                        data.extend(
                            map(
                                lambda row_data: [city] + row_data,
                                map(
                                    lambda i: list(
                                        map(lambda col_index: column_value_index(driver,col_index, i + 1), column_indexs)),
                                    range(len(rows))
                                )
                            )
                        )
                    except Exception as e:
                        print(f"Error extracting data: {e}")

                    results_df = pd.DataFrame(data, columns=columns)
                    print(results_df.head())

                    # Save the results to a CSV file
                    results_df.to_csv("scraped_data.csv", index=False, encoding='utf-8-sig')
                    print("Data saved to scraped_data.csv")

            except (NoSuchElementException, TimeoutException):
                print("Table or rows not found.")
                continue
        iteration_count += 1
    # Create a DataFrame to store the results
    results_df = pd.DataFrame(data, columns=columns)
    print(results_df.head())

    # Save the results to a CSV file
    results_df.to_csv("scraped_data.csv", index=False, encoding='utf-8')
    print("Data saved to scraped_data.csv")

    driver.quit()

if __name__ == "__main__":
    create_dataset()
