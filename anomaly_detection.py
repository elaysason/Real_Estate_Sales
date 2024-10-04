import sqlite3
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import get_driver
import pandas as pd
import chardet
import psycopg2


def restart_driver(driver):
    print("Restarting driver to maintain connection...")
    driver.quit()
    time.sleep(2)  # Small delay to ensure proper shutdown
    return get_driver()


def write_last_processed_index(file_path, index):
    """Writes the last processed index to the text file."""
    with open(file_path, 'w') as f:
        f.write(str(index))


def column_value_index(driver, column_index, row_index):
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


def extend_data_with_city(data, city, driver, column_indexes, rows):
    extracted_data = map(
        lambda row_data: [city] + row_data,
        map(
            lambda i: list(
                map(lambda col_index: column_value_index(driver, col_index, i + 1), column_indexes)
            ),
            range(len(rows))
        )
    )
    data.extend(extracted_data)
    return data


def map_rooms_to_float(rooms):
    """Maps room descriptions to float values."""
    room_mapping = {
        "ראשונה": 1.0,
        "שנייה": 2.0,
        "שלישית": 3.0,
        "רביעית": 4.0,
        "חמישית": 5.0,
        "שישית": 6.0,
        "שביעית": 7.0,
        "שמינית": 8.0,
        "תשיעית": 9.0,
        "עשירית": 10.0,
        "אחת עשרה": 11.0,
        "שנים עשרה": 12.0
    }
    return room_mapping.get(rooms.strip(), None)  # Return None if not found


def insert_into_db(data):
    """Inserts a list of real estate records into the database more efficiently."""
    # PostgreSQL connection
    conn = psycopg2.connect(database='real_estate_db', user='postgres', password='1q2w3e', host='localhost',
                            port='5432')
    cursor = conn.cursor()

    # SQL command with `ON CONFLICT DO NOTHING` for PostgreSQL
    sql_command = '''
        INSERT INTO sales (city, sale_date, address, block_parcel, property_type, rooms, floor, square_meters, amount, trend_change)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (city, sale_date, address, amount) DO NOTHING;
    '''

    # Trim whitespace for all string fields in one go before insertion
    trimmed_data = [
        (
            record[0].strip(),  # city
            record[1],  # sale_date (assuming it's already in the correct format)
            record[2].strip(),  # address
            record[3].strip(),  # block_parcel
            record[4].strip(),  # property_type
            float(record[5]) if record[5] else None,  # rooms
            map_rooms_to_float(record[6]),  # floor
            float(record[7]) if record[7] else None,  # square_meters
            int(record[8].replace(',', '')) if record[8] else None,  # amount
            record[9].strip()  # trend_change
        )
        for record in data
    ]

    # Use `executemany` to insert all the data in one go for better efficiency
    cursor.executemany(sql_command, trimmed_data)

    # Count how many records were inserted
    inserted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return inserted_count


def create_dataset():
    # Initialize driver
    # Ensure get_driver() is correctly defined in your utils

    # Detect encoding and read the city list
    with open("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    cities = pd.read_csv("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", encoding=encoding)

    # Initialize an empty list to store scraped data

    driver = get_driver()

    restart_threshold = 10  # Set the number of iterations before restarting
    with open("./latest_city.txt", 'r') as f:
        latest_index = int(f.read().strip())
    column_indexes = list(range(1, 10))

    # Loop through each city
    for index, city in enumerate(cities["שם_ישוב"][latest_index:], start=latest_index):
        data = []
        if index % restart_threshold == 0 and index != 0:
            driver = restart_driver(driver)
        print(f"Searching for city: {city}")
        driver.get("https://www.nadlan.gov.il/")

        try:
            # Wait for the search box and enter the city name
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="SearchString"]'))
            )
            search_box.send_keys(city.strip())
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
        time.sleep(10)

        # Check if still on the search page
        if driver.current_url == "https://www.nadlan.gov.il/":
            print("Not found, retrying...")
            try:
                search_box = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="SearchString"]')))
                search_box.clear()
            except NoSuchElementException:
                print("Search box not found on retry.")
            continue
        else:
            print("Data found, loading results...")

            columns = ['city'] + [WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '/html/body/div[2]/div[2]/div[2]/div[1]/div[2]/div[5]/button[' + str(
                        i) + ']'))).text for i in
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
                    time.sleep(10)  # Wait for the new rows to load
                    rows = table.find_elements(By.CLASS_NAME, "tableRow")
                    number_of_rows = len(rows)
                    print(f"Rows found: {number_of_rows}")

                    # Break if no new rows are loaded
                    if number_of_rows == previous_number_of_rows:
                        break
                    previous_number_of_rows = number_of_rows
                    if number_of_rows % 1000 == 0:
                        extended_data = extend_data_with_city(data, city, driver, column_indexes, rows)
                        inserted = insert_into_db(extended_data)
                        print(f"Inserted {inserted} records into the database")
                        data = []
                # Extract data from the rows if found
                if number_of_rows == 0:
                    print("0 records of sales found")
                    continue
                else:
                    print(f"Total rows found after scrolling: {number_of_rows}")
                    # Extract data from each row
                    try:
                        # Use enumerate with map to extract data for each row and column
                        extended_data = extend_data_with_city(data, city, driver, column_indexes, rows)
                        inesrted = insert_into_db(extended_data)
                        print(f"Inserted {inesrted} records into the database")

                    except Exception as e:
                        print(f"Error extracting data: {e}")

            except (NoSuchElementException, TimeoutException):
                print("Table or rows not found.")
                continue
        write_last_processed_index('./latest_city.txt', index)

    # Save the results to a CSV file

    driver.quit()


if __name__ == "__main__":
    create_dataset()
