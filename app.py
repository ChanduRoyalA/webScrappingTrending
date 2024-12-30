from flask import Flask, render_template, jsonify, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from datetime import datetime
import uuid
import os
import time

app = Flask(__name__)

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017/"  # Replace with your MongoDB URI
client = MongoClient(MONGO_URI)
db = client['twitter_trends']
collection = db['trending_topics']

# Environment variables for credentials
USERNAME = os.getenv("TWITTER_USERNAME", "chanduroyal7102")  # Replace with your username
PASSWORD = os.getenv("TWITTER_PASSWORD", "chandu@7102")  # Replace with your password
PAC_FILE_PATH = "us-ca.pac"  # Replace with the full path to your PAC file

# Selenium setup function
def fetch_trending_topics():
    options = Options()
    options.add_argument(f'--proxy-pac-url={PAC_FILE_PATH}')
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    try:
        # Log in to Twitter
        driver.get("https://twitter.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "text")))

        username = driver.find_element(By.NAME, "text")
        username.send_keys(USERNAME)
        username.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
        password = driver.find_element(By.NAME, "password")
        password.send_keys(PASSWORD)
        password.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(EC.url_contains("home"))

        # Fetch trending topics
        driver.get("https://twitter.com/home")
        trending_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//section[contains(., 'What’s happening')]"))
        )
        trends = trending_section.find_elements(By.XPATH, ".//div[@data-testid='trend']//span")

        trending_topics = [trend.text for trend in trends[:5]]

        # Record details for MongoDB
        unique_id = str(uuid.uuid4())
        ip_address = "Extracted from PAC file or external service"  # Replace with logic to fetch IP if needed
        current_time = datetime.now()

        data = {
            "unique_id": unique_id,
            "trend1": trending_topics[0] if len(trending_topics) > 0 else None,
            "trend2": trending_topics[1] if len(trending_topics) > 1 else None,
            "trend3": trending_topics[2] if len(trending_topics) > 2 else None,
            "trend4": trending_topics[3] if len(trending_topics) > 3 else None,
            "trend5": trending_topics[4] if len(trending_topics) > 4 else None,
            "datetime": current_time,
            "ip_address": ip_address
        }

        # Insert into MongoDB
        collection.insert_one(data)
        return data

    except Exception as e:
        return {"error": str(e)}

    finally:
        driver.quit()

# Flask Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run_script")
def run_script():
    data = fetch_trending_topics()
    return render_template("result.html", data=data)

@app.route("/get_data")
def get_data():
    records = list(collection.find())
    for record in records:
        record["_id"] = str(record["_id"])
    return jsonify(records)

if __name__ == "__main__":
    app.run(debug=True)
