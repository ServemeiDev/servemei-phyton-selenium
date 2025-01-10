import os
import pickle
from flask import Flask, jsonify, request
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
import logging
import sys
import random
import time
from selenium import webdriver
import undetected_chromedriver as udc
from fake_useragent import UserAgent
from selenium.webdriver.common.proxy import Proxy, ProxyType
from extension import proxies

logging.basicConfig(
    format="%(levelname)s:%(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("/tmp/out.log"), logging.StreamHandler(sys.stdout)],
)

app = Flask(__name__)


class Prenota:
    @staticmethod
    def run(cnpj):
        proxies_extension = proxies('spphm86cju', 'ik18bprcRnN4OxU=3d', 'gate.smartproxy.com', '7000')
        chrome_options = udc.ChromeOptions()
        chrome_options.headless = True
        chrome_options.add_extension(proxies_extension)
       
        chrome_options.add_argument("--disable-gpu")  # Desabilita aceleração de GPU (necessário no modo headless)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Evita que o Chrome seja detectado como automatizado 
        ua = UserAgent()
        user_agent = ua.random
        chrome_options.add_argument(f'--user-agent={user_agent}')
        driver = udc.Chrome(use_subprocess=True, options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        })
    
       
        try:            
            url = f'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/mobile/{cnpj}'
            driver.get(url)
            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/'
            WebDriverWait(driver, 20).until(EC.url_to_be(expected_url))
            cookies = driver.get_cookies()
            print("Cookies:", cookies)
            driver.quit()
            return {"status": "success", "cookies": cookies}
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
    # Configuração de produção
    app.run(host="0.0.0.0", port=5000, debug=False)
