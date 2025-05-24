import logging
import time

from selenium.webdriver.chrome.options import Options
from selenium import webdriver


def get_driver(link):
    """
    Initializes and returns a Chrome WebDriver instance in the government site in headless mode.

    Returns:
        webdriver.Chrome: A Chrome WebDriver instance with the specified options.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    driver.get(link)
    return driver
def validate_parameters(args):
    """
    A function that validates the parameters passed to the script.

    Args:
        args: A list of arguments to be validated.

    Raises:
        ValueError: If the number of arguments is not equal to 2.
    """
    if len(args) != 2:
        raise ValueError("Usage: sales_notification.py <config_file_path>")


def validate_config(test_config):
    """
    Validate the configuration dictionary against a list of required keys and their corresponding values.

    Args:
        test_config (dict): The configuration dictionary to be validated.

    Raises:
        ValueError: If any of the required keys are missing or if the 'sender_email' or any of the 'receiver_emails'
                    are not valid email addresses.

    Returns:
        None
    """
    # Ensure all required keys are present
    required_keys = ['desired_location', 'sender_email', 'receiver_emails', 'email_password']
    for key in required_keys:
        if key not in test_config:
            raise ValueError(f"JSON format error: Missing required key '{key}'.")

    # Ensure sender_email is a valid email format (basic check)
    if '@' not in test_config['sender_email']:
        raise ValueError("JSON format error: 'sender_email' is not a valid email address.")

    # Ensure receiver_emails is a list and contains valid email addresses
    if not isinstance(test_config['receiver_emails'], list):
        raise ValueError("JSON format error: 'receiver_emails' must be a list.")
    for email in test_config['receiver_emails']:
        if '@' not in email:
            raise ValueError(f"JSON format error: Invalid email address in 'receiver_emails': {email}")


def restart_driver(driver):
    logging.info("Restarting driver to maintain connection...")
    driver.quit()
    time.sleep(2)
    return get_driver()