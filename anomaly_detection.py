import requests
import json
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import get_driver, restart_driver
import pandas as pd
import chardet
import psycopg2
import io
from difflib import get_close_matches
from decouple import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_HOST = config('DB_HOST')
DB_NAME = config('DB_NAME')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_PORT = config('DB_PORT')
ROWS_PER_PAGE = 10
ROWS_PER_REQUEST = 500


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


floor_dict = {
    "ראשונה": 1, "א": 1,
    "שנייה": 2, "ב": 2,
    "שלישית": 3, "ג": 3,
    "רביעית": 4, "ד": 4,
    "חמישית": 5, "ה": 5,
    "שישית": 6, "ו": 6,
    "שביעית": 7, "ז": 7,
    "שמינית": 8, "ח": 8,
    "תשיעית": 9, "ט": 9,
    "עשירית": 10, "י": 10,
    "אחת עשרה": 11, "יא": 11,
    "שנים עשרה": 12, "יב": 12,
    "שלוש עשרה": 13, "יג": 13,
    "ארבע עשרה": 14, "יד": 14,
    "חמש עשרה": 15, "טו": 15,
    "שש עשרה": 16, "טז": 16,
    "שבע עשרה": 17, "יז": 17,
    "שמונה עשרה": 18, "יח": 18,
    "תשע עשרה": 19, "יט": 19,
    "עשרים": 20, "כ": 20,
    "קרקע": 0, "קומת קרקע": 0,
    "מרתף": -1, "מינוס": -1
}


def detect_floor_number(floor_name):
    if not floor_name:
        return None

    floor_name = floor_name.strip()
    closest_match = get_close_matches(floor_name, floor_dict.keys(), n=1, cutoff=0.8)

    if closest_match:
        return floor_dict[closest_match[0]]

    return None


def insert_city(city_id, city_name, county_id, council_id):
    """
    Insert a city by ID and name. If a city with the same name already exists, skip the insertion.
    """
    try:
        with psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO city (id, name, county_id, council_id) 
                    VALUES (%s, %s, %s, %s) 
                    ON CONFLICT (name) DO NOTHING
                """, (city_id, city_name, county_id, council_id))

                # Check if the row was inserted
                if cursor.rowcount > 0:
                    logging.info(f"Successfully inserted city: {city_name} with ID: {city_id}")
                else:
                    logging.info(f"City {city_name} already exists. Skipping insertion.")

                conn.commit()  # Commit the transaction
    except Exception as e:
        logging.error(f"Error inserting city {city_name}: {e}")
        raise


def insert_county(county_id, county_name):
    """
    Insert or update a county by ID and name, then return the ID
    """
    try:
        with psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO county (id, name) 
                    VALUES (%s, %s) 
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name 
                    RETURNING id
                """, (county_id, county_name))
                conn.commit()
                logging.info(f"Successfully inserted/updated county: {county_name} with ID: {county_id}")
    except Exception as e:
        logging.error(f"Error inserting county {county_name}: {e}")
        raise


def insert_council(council_id, council_name):
    """
    Insert or update a council by ID and name, then return the ID
    """
    try:
        with psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO council (id, name) 
                    VALUES (%s, %s) 
                    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name 
                    RETURNING id
                """, (council_id, council_name))
                conn.commit()
                logging.info(f"Successfully inserted/updated council: {council_name} with ID: {council_id}")
    except Exception as e:
        logging.error(f"Error inserting council {council_name}: {e}")
        raise


def insert_into_db(data,total_sales):
    try:
        with psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                sales_rows_affected = 0  # Initialize counter for sales rows

                for record in data['data']['items']:
                    if sales_rows_affected >= total_sales:
                        logging.info(f"Processed required number of records ({total_sales})")
                        break
                    neighborhood_exists = False

                    # Insert neighborhood or retrieve its ID if it already exists
                    if record['neighborhoodName'] is not None:
                        cursor.execute("""
                            INSERT INTO neighborhood (id, name, city_id) 
                            VALUES (%s, %s, %s) 
                            ON CONFLICT (name, city_id) DO NOTHING
                        """, (
                            record['neighborhoodId'],
                            record['neighborhoodName'],
                            record['settlmentID']
                        ))

                        # Check if the neighborhood was inserted
                        if cursor.rowcount == 0:
                            cursor.execute("""
                                SELECT id FROM neighborhood 
                                WHERE name = %s AND city_id = %s
                            """, (record['neighborhoodName'], record['settlmentID']))
                            existing_neighborhood = cursor.fetchone()
                            if existing_neighborhood:
                                neighborhood_id = existing_neighborhood[0]
                                logging.info(
                                    f"Retrieved existing neighborhood ID {neighborhood_id} for neighborhood: {record['neighborhoodName']}")
                        else:
                            neighborhood_id = record['neighborhoodId']
                            logging.info(
                                f"Successfully inserted neighborhood: {record['neighborhoodName']} with ID: {neighborhood_id}")
                        neighborhood_exists = True
                    else:
                        logging.warning(
                            f"Skipped neighborhood insertion due to null name for ID: {record['neighborhoodId']}")
                        neighborhood_id = None

                    # Insert building if neighborhood_id is available
                    cursor.execute("""
                        INSERT INTO building (
                            id,
                            neighborhood_id, 
                            parcel_num, 
                            address,
                            total_floors,
                            year_built,
                            city_id
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id, parcel_num) DO UPDATE SET 
                            parcel_num = EXCLUDED.parcel_num,
                            address = EXCLUDED.address,
                            total_floors = EXCLUDED.total_floors,
                            year_built = EXCLUDED.year_built,
                            city_id = EXCLUDED.city_id
                    """, (
                        record['addressId'],
                        neighborhood_id,
                        record['parcelNum'],
                        record['address'],
                        record.get('buildingFloors', 0),
                        record.get('yearBuilt', 0),
                        record['settlmentID']
                    ))

                    logging.info(
                        f"Successfully inserted/updated building with ID: {record['addressId']} at address: {record['address']}")

                    # Handle property type
                    deal_nature = record['dealNature']
                    if deal_nature is not None:
                        deal_nature = deal_nature.replace("'", "")
                        cursor.execute("SELECT id FROM property_type WHERE name = %s", (deal_nature,))
                        property_type_result = cursor.fetchone()
                        property_type_id = property_type_result[0] if property_type_result else 6
                    else:
                        property_type_id = 6

                    if property_type_id is None:
                        logging.warning(
                            f"Property type ID for '{deal_nature}' does not exist. Skipping asset insertion.")
                        continue

                    asset_id = record['assetId'] if record['assetId'] is not None else 0

                    # Insert asset
                    cursor.execute("""
                        INSERT INTO asset (
                            id,
                            building_id,
                            parcel_num, 
                            property_type_id,
                            floor,
                            square_meters,
                            rooms
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id, parcel_num) DO UPDATE SET 
                            building_id = EXCLUDED.building_id,
                            parcel_num = EXCLUDED.parcel_num,
                            property_type_id = EXCLUDED.property_type_id,
                            floor = EXCLUDED.floor,
                            square_meters = EXCLUDED.square_meters,
                            rooms = EXCLUDED.rooms
                    """, (
                        asset_id,
                        record['addressId'],
                        record['parcelNum'],
                        property_type_id,
                        detect_floor_number(record['floor']),
                        record['assetArea'],
                        record['roomNum']
                    ))

                    logging.info(
                        f"Successfully inserted/updated asset with ID: {record['assetId']} in building: {record['addressId']}")

                    # Insert sale
                    cursor.execute("""
                        INSERT INTO sales (
                            asset_id,
                            sale_date,
                            amount,
                            price_per_sqm,
                            trend_rate,
                            trend_years,
                            parcel_num,
                            city_id
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        asset_id,
                        record['dealDate'],
                        record['dealAmount'],
                        record['priceSM'],
                        record['trend']['rate'],
                        record['trend']['years'],
                        record['parcelNum'],
                        record['settlmentID']
                    ))

                    # Only update the counter for rows affected by sales insertion
                    sales_rows_affected += cursor.rowcount

                    logging.info(
                        f"Successfully inserted SALE for asset: {record['assetId']}, amount: {record['dealAmount']}, date: {record['dealDate']}")

                # Commit and log total sales rows affected
                conn.commit()
                return sales_rows_affected


    except Exception as e:
        logging.error(f"Error inserting data into the database: {e}")
        return 0


# Batch processing function for better performance
def batch_insert_into_db(data_batch, batch_size=1000):
    """
    Process data in batches for better performance
    """
    try:
        with psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                # Prepare the statements
                statements = {
                    'cities': [],
                    'neighborhoods': [],
                    'buildings': [],
                    'assets': [],
                    'sales': []
                }

                for i in range(0, len(data_batch), batch_size):
                    batch = data_batch[i:i + batch_size]

                    # Execute batch inserts using execute_values
                    from psycopg2.extras import execute_values

                    # Example for cities batch insert:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO city (name) 
                        VALUES %s 
                        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                        """,
                        [(record['settlmentName'],) for record in batch]
                    )

                conn.commit()
                return len(data_batch)

    except Exception as e:
        logging.error(f"Error in batch insert: {e}")
        return 0


def city_page_validation(driver, city):
    if driver.current_url == "https://dev.nadlan.gov.il/":
        return False

    try:

        city_page = driver.find_element(By.CSS_SELECTOR, 'a.locationLink')
        return city_page.text.strip() == city

    except NoSuchElementException:
        return False


def get_first_match(driver, city):
    index = 0
    found = False

    while not found:
        try:
            xpath = f'//*[@id="react-autowhatever-1--item-{index}"]'
            item = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            item_values = item.text.split('\n')
            if item_values[1] == 'יישוב':
                if item_values[0] == city:
                    print(f'Found city: {item.text}')
                    return item
                else:
                    index += 1
            else:
                return None

        except Exception as e:
            logging.info("Not found, retrying...")
            break


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
        city = city.strip()
        county_index = int(cities["סמל_לשכת_מנא"][index])
        county_name = cities["לשכה"][index].strip()
        council_index = int(cities["סמל_מועצה_איזורית"][index])
        council_name = cities["שם_מועצה"][index]
        if isinstance(council_name, str):
            council_name = council_name.strip()

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
                search_box.send_keys(city + Keys.RETURN)

                search_button = get_first_match(driver, city)
                if search_button is None:
                    logging.info(f"Not found, retrying... (Retry {retry_count}/{max_retries})")
                    driver.get("https://dev.nadlan.gov.il/")
                    retry_count += 1
                    continue
                search_button.click()
                break
            except TimeoutException:
                logging.warning(f"Timed out waiting for elements on {driver.current_url}")
                logging.info(f"Not found, retrying... (Retry {retry_count}/{max_retries})")

                retry_count += 1
        time.sleep(10)
        if not city_page_validation(driver, city):
            logging.info("Not found, moving on to next city...")
            continue
        else:
            base_id = driver.current_url.split('&')[1].split('=')[1]
            total_deals = driver.find_element(By.CSS_SELECTOR, "div.tableSummary p.plainText").text.split(
                ' ')[1]
            logging.info("Data found, loading results... totals rows " + str(total_deals))
            insert_council(council_index, council_name)
            insert_county(county_index, county_name)
            insert_city(base_id, city, county_index, council_index)
            if int(total_deals) > 0:
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
                    requests_number = int(int(total_deals) / ROWS_PER_REQUEST) + 1
                    last_sales_number = int(total_deals) % ROWS_PER_REQUEST
                    for fetch_number in range(1, requests_number+1):
                        response = requests.post(url, json=body)
                        print(f"Status Code: {response.status_code}")
                        response_data = json.loads(response.text)
                        if fetch_number != requests_number:
                            inserted_rows = insert_into_db(response_data,ROWS_PER_REQUEST)
                        else:
                            inserted_rows = insert_into_db(response_data,last_sales_number)
                        logging.info(str(fetch_number) + " batch loaded having " + str(
                            inserted_rows) + " rows")


                #
                except (NoSuchElementException, TimeoutException):
                    logging.error("Table or rows not found.")
                    continue

        write_last_processed_index('./latest_city.txt', index)

    driver.quit()


if __name__ == "__main__":
    create_dataset()
