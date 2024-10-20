import requests
import json
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import get_driver
import pandas as pd
import chardet
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ROWS_PER_PAGE = 10
ROWS_PER_REQUEST = 500

def restart_driver(driver):
    logging.info("Restarting driver to maintain connection...")
    driver.quit()
    time.sleep(2)
    return get_driver()


def write_last_processed_index(file_path, index):
    with open(file_path, 'w') as f:
        f.write(str(index))


def column_value_index(driver, column_index, row_index):
    xpath = f'/html/body/div[2]/div[2]/div[2]/div[1]/div[3]/div/grid-directive/div/div[{row_index}]/button/div[{column_index}]'
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip()
    except NoSuchElementException:
        logging.warning(f"Element not found for XPath: {xpath}")
        return "N/A"
    except Exception as e:
        logging.error(f"Error in locating element: {e}")
        return "N/A"


def extend_data_with_city(data, city, driver, column_indexes, rows):
    extracted_data = [
        [city] + [column_value_index(driver, col_index, i + 1) for col_index in column_indexes]
        for i in range(len(rows))
    ]
    data.extend(extracted_data)
    return data


def map_rooms_to_float(rooms):
    room_mapping = {
        "ראשונה": 1.0, "שנייה": 2.0, "שלישית": 3.0, "רביעית": 4.0,
        "חמישית": 5.0, "שישית": 6.0, "שביעית": 7.0, "שמינית": 8.0,
        "תשיעית": 9.0, "עשירית": 10.0, "אחת עשרה": 11.0, "שנים עשרה": 12.0
    }
    return room_mapping.get(rooms.strip(), None)


import io


def insert_into_db(data):
    try:
        # Establish a connection to the PostgreSQL database
        with psycopg2.connect(database='real_estate_db', user='postgres', password='1q2w3e', host='localhost',
                              port='5432') as conn:
            with conn.cursor() as cursor:
                # Create a StringIO object to hold the data for COPY
                buffer = io.StringIO()

                # Prepare the data for COPY
                for record in data:
                    # Replace None with \N for COPY compatibility
                    buffer.write(
                        "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                            record[0].strip(),
                            record[1],
                            record[2].strip(),
                            record[3].strip(),
                            record[4].strip(),
                            float(record[5]) if record[5] not in [None, ''] else '\\N',
                            # Check for None or empty string
                            map_rooms_to_float(record[6]) if record[6] not in [None, ''] else '\\N',
                            # Check for None or empty string
                            float(record[7]) if record[7] not in [None, ''] else '\\N',
                            # Check for None or empty string
                            int(record[8].replace(',', '')) if record[8] not in [None, ''] else '\\N',
                            # Check for None or empty string
                            record[9].strip()
                        )
                    )

                # Move the cursor to the beginning of the StringIO buffer
                buffer.seek(0)

                # Use the COPY command to insert data
                cursor.copy_from(buffer, 'sales', sep='\t', columns=(
                    'city', 'sale_date', 'address', 'block_parcel',
                    'property_type', 'rooms', 'floor', 'square_meters',
                    'amount', 'trend_change'
                ))

                # Commit the transaction
                conn.commit()

                return len(data)  # Return the total number of records inserted

    except Exception as e:
        logging.error(f"Error inserting data into the database: {e}")
        return 0  # Return 0 if there was an error


def insert_into_db111(data):
    with psycopg2.connect(database='real_estate_db', user='postgres', password='1q2w3e', host='localhost',
                          port='5432') as conn:
        with conn.cursor() as cursor:
            sql_command = '''
                INSERT INTO sales (city, sale_date, address, block_parcel, property_type, rooms, floor, square_meters, amount, trend_change)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city, sale_date, address, amount) DO NOTHING;
            '''
            trimmed_data = [
                (
                    record[0].strip(),
                    record[1],
                    record[2].strip(),
                    record[3].strip(),
                    record[4].strip(),
                    float(record[5]) if record[5] else None,
                    map_rooms_to_float(record[6]),
                    float(record[7]) if record[7] else None,
                    int(record[8].replace(',', '')) if record[8] else None,
                    record[9].strip()
                )
                for record in data
            ]
            cursor.executemany(sql_command, trimmed_data)
            return cursor.rowcount


def get_first_match(driver, city):
    index = 0
    found = False

    while not found:
        try:
            # Create the dynamic XPath for the current item
            xpath = f'//*[@id="react-autowhatever-1--item-{index}"]'

            # Wait for the item to be present
            item = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            item_values = item.text.split('\n')
            # Get the font-weight style of the item
            city_colour = item.value_of_css_property('color')

            # Check if the font weight indicates bold
            if item_values[1] == 'יישוב':
                if item_values[0] == city:
                    print(f'Found city: {item.text}')
                    return item  # Click the bold item
                else:
                    index += 1
            else:
                return None

        except Exception as e:
            logging.info("Not found, retrying...")
            break  # Exit the loop if no more items are found


def create_dataset():
    with open("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    cities = pd.read_csv("C:/Users/User/PycharmProjects/scraping_sales/cities.csv", encoding=encoding)

    driver = get_driver()
    restart_threshold = 10
    with open("./latest_city.txt", 'r') as f:
        latest_index = int(f.read().strip())
    column_indexes = list(range(1, 10))

    for index, city in enumerate(cities["שם_ישוב"][latest_index:], start=latest_index):
        data = []
        if index % restart_threshold == 0 and index != 0:
            driver = restart_driver(driver)
        logging.info(f"Searching for city: {city}")
        max_retries = 5
        retry_count = 0
        driver.get("https://dev.nadlan.gov.il/")
        while retry_count < max_retries:
            try:
                search_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="myInput2"]'))
                )
                search_box.send_keys(city.strip() + Keys.RETURN)

                search_button = get_first_match(driver, city.strip())
                if search_button is None:
                    logging.info(f"Not found, retrying... (Retry {retry_count}/{max_retries})")
                    retry_count += 1
                    continue
                search_button.click()
                break
            except TimeoutException:
                logging.warning(f"Timed out waiting for elements on {driver.current_url}")
                logging.info(f"Not found, retrying... (Retry {retry_count}/{max_retries})")

                retry_count += 1

        if driver.current_url == "https://dev.nadlan.gov.il/":
            logging.info("Not found, moving on to next city...")
            continue
        else:
            base_id = driver.current_url.split('&')[1].split('=')[1]
            total_deals = driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div/div[2]/div/div/div/div[2]/section[2]/div/div[2]/div/div[2]/p').text.split(' ')[1]
            logging.info("Data found, loading results... totals rows " + str(total_deals))

            try:
                fetch_number = 1
                url = "https://x4006fhmy5.execute-api.il-central-1.amazonaws.com/api/deal"
                body = {
                    "base_id": base_id,
                    "base_name": "settlmentID",
                    "fetch_number": str(fetch_number),
                    "type_order": "dealDate_down",
                    "sk": "eyJhbGciOiJIUzI1NiJ9.eyJkb21haW4iOiJkZXYubmFkbGFuLmdvdi5pbCIsImV4cCI6MTcyOTQxOTY3NH0.nwjNBPOn2xKgtoREu2McVZjPRevomyAedyUrHav2wV4"
                }
                requests_number = int(int(total_deals)/ROWS_PER_REQUEST)+1
                for fetch_number in range(1, requests_number):
                    response = requests.post(url, json=body)
                    response_data = json.loads(response.text)
                print(f"Status Code: {response.status_code}")
                logging.info("Data found, loading results... totals rows " + str(total_deals))

                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "myTable"))
                )

                previous_number_of_rows = 0
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    WebDriverWait(driver, 10).until(
                        lambda d: len(table.find_elements(By.CLASS_NAME, "tableRow")) > previous_number_of_rows
                    )

                    rows = table.find_elements(By.CLASS_NAME, "tableRow")
                    number_of_rows = len(rows)
                    logging.info(f"Rows found: {number_of_rows}")

                    if number_of_rows == previous_number_of_rows:
                        break
                    previous_number_of_rows = number_of_rows

                    if number_of_rows % 1000 == 0 and not (city == "עפולה" and number_of_rows < 8000):
                        extended_data = extend_data_with_city(data, city, driver, column_indexes, rows)
                        inserted = insert_into_db(extended_data)
                        logging.info(f"Inserted {inserted} records into the database")
                        data = []

                if number_of_rows > 0:
                    extended_data = extend_data_with_city(data, city, driver, column_indexes, rows)
                    inserted = insert_into_db(extended_data)
                    logging.info(f"Inserted {inserted} records into the database")
                else:
                    logging.info("0 records of sales found")

            except (NoSuchElementException, TimeoutException):
                logging.error("Table or rows not found.")
                continue

        write_last_processed_index('./latest_city.txt', index)

    driver.quit()


if __name__ == "__main__":
    create_dataset()
