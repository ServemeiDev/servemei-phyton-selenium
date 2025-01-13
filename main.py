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
from selenium.webdriver.common.action_chains import ActionChains 

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
            # URL com o CNPJ passado dinamicamente
            url = f'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/mobile/{cnpj}'
            driver.get(url)
            # Verifique a URL atual
            time.sleep(3) 
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

    @staticmethod
    def runDas(cnpj):
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
            # URL com o CNPJ passado dinamicamente
            url = f'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao'
            driver.get(url)
            time.sleep(2) 
            # Verifique a URL atual
            input_element = driver.find_element(By.CSS_SELECTOR, "#cnpj")
            input_element.clear()
            input_element.send_keys(cnpj)
            time.sleep(2) 

            continuar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#continuar")))
            continuar_button.click()

            time.sleep(2) 
            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Home/Inicio'
            WebDriverWait(driver, 20).until(EC.url_to_be(expected_url))
            cookies = driver.get_cookies()
            driver.quit()
            return {"status": "success", "cookies": cookies}
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e), "cookies": []}

@app.route("/dasn", methods=["POST"])
def start_prenota():
    # Obtém o CNPJ do corpo da requisição
    data = request.get_json()
    cnpj = data.get("cnpj")
    print(cnpj)
    
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400

  
    response = Prenota.run(cnpj)
    return jsonify(response)

@app.route("/das", methods=["POST"])
def start_prenota_das():
    # Obtém o CNPJ do corpo da requisição
    data = request.get_json()
    cnpj = data.get("cnpj")
    print(cnpj)
    
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400

  
    response = Prenota.runDas(cnpj)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)