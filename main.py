import os
import pickle
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import Select
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import logging
import yaml
import sys
import time
import random
import undetected_chromedriver as udc
from fake_useragent import UserAgent

logging.basicConfig(
    format="%(levelname)s:%(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("/tmp/out.log"), logging.StreamHandler(sys.stdout)],
)

app = Flask(__name__)

class Prenota:
    @staticmethod
    def run(cnpj):
        options = udc.ChromeOptions()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'--user-agent={user_agent}')
        driver = udc.Chrome(use_subprocess=True, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        })
        try:
            url = f'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/mobile/{cnpj}'
            driver.get(url)
            pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))
            cookies = pickle.load(open("cookies.pkl", "rb"))
            cookies_info = []
            for cookie in cookies:
                cookies_info.append(cookie)
            driver.quit()
            return {"status": "success", "cookies": cookies_info}
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e)}

@app.route("/", methods=["POST"])
def start_prenota():
    data = request.get_json()
    cnpj = data.get("cnpj")
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400
    response = Prenota.run(cnpj)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
