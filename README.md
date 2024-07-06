# Real Estate Sales

## Introduction
This project is a Real Estate Sales Notification System that automates the process of monitoring new property sales on a specified website. When a new sale is detected, the system sends an email notification with the sale details.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)
- [License](#license)

## Features
- Automated search for new real estate sales on the finshed sales gov website.
- Sends email notifications with the details of new sales.
- Generates an HTML file with a map pinpointing the location of the new sale.
- Uses Selenium for web automation
## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/elaysason/real_estate_sales.git
   cd real_estate_sales
   ```

## Usage
1. Ensure you have Chrome installed and the ChromeDriver executable is in your PATH.
2. Create a configuration JSON file (e.g., `config.json`) with the following structure:
   ```json
   {
       "desired_location": "example_area",
       "sender_email": "mail_example@gmail.com",
       "receiver_emails": ["reciver_1@gmail.com", "reciver_2@gmail.com"],
       "email_password": "PASSWORD"
   }
   ```
3. Run the script with the path to your configuration file:
   ```bash
   python sales_notification.py config.json
   ```

## Configuration
- **Email Configuration:** Set the `sender_email`, `receiver_emails`, and `email_password` variables in the configuration file.
- **Search Place:** Update the `desired_location` in the configuration file with the desired search location.

## Dependencies
- Python 3.x
- Selenium
- smtplib
- email

Install dependencies via:
```bash
pip install selenium smtplib email
```

## Examples
To search for new sales in a specific area and send notifications, make sure your `config.json` file is correctly set up and run:
```bash
python sales_notification.py config.json
```


## Troubleshooting
- **Issue:** No new sale detected even though there should be one.
  - **Solution:** Ensure the XPath expressions used to locate web elements are correct and up-to-date with the website's structure.
  
- **Issue:** Email not being sent.
  - **Solution:** Verify the SMTP configuration and ensure less secure app access is enabled for the sender's email account.


---
