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
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.common.keys import Keys 
import requests
import undetected_chromedriver as uc

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
            current_url = driver.current_url
            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/'

            if current_url == expected_url:
                cookies = driver.get_cookies()
                print("Cookies:", cookies, current_url)
                driver.quit()
                return {"status": "success", "cookies": cookies}
            else:
                print(f"A URL atual é {current_url}, não a esperada.")
                
            driver.quit()
            return {"status": "error", "message": "URL não corresponde"}
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
            current_url = driver.current_url
            print("URL:", current_url)
            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Home/Inicio'

            if current_url == expected_url:
                cookies = driver.get_cookies()
                print("Cookies:", cookies, current_url)
                driver.quit()
                return {"status": "success", "cookies": cookies}
            else:
                print(f"A URL atual é {current_url}, não a esperada.")
                
            driver.quit()
            return {"status": "error", "message": "URL não corresponde", "cookies": []}
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e), "cookies": []}

    @staticmethod
    def runCCMEI():
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'--user-agent={user_agent}')
        driver = uc.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        })

        driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            window.outerWidth = 1366;
            window.outerHeight = 768;
            window.innerWidth = 1366;
            window.innerHeight = 768;
            window.screenX = 0;
            window.screenY = 0;
            window.screen.availWidth = 1366;
            window.screen.availHeight = 768;
            window.screen.width = 1366;
            window.screen.height = 768;
        """)

        try:
            # URL com o CNPJ passado dinamicamente
            url = f'https://sso.acesso.gov.br/authorize?response_type=code&client_id=mei.receita.economia.gov.br&scope=openid+email+phone+profile+govbr_confiabilidades&redirect_uri=https%3A%2F%2Fmei.receita.economia.gov.br%2Fcertificado%2Fgovbrlogincallback&nonce=dd626124-b349-4444-99cc-471df58cc4f3'
            driver.get(url)

            some_element = driver.find_element(By.CSS_SELECTOR, "#accountId")
            action = ActionChains(driver)
            action.move_to_element(some_element).click().perform()
            time.sleep(2)
            input_element_accountId = driver.find_element(By.CSS_SELECTOR, "#accountId")
            input_element_accountId.send_keys("05485547575")
            input_element_accountId.send_keys(Keys.RETURN) 
            time.sleep(2) 
            input_element_password = driver.find_element(By.CSS_SELECTOR, "#password")
            input_element_password.send_keys("123456789")
            input_element_password.send_keys(Keys.RETURN) 
            time.sleep(5)
            wait = WebDriverWait(driver, 1)  # Espera de 10 segundos até o elemento aparecer
            input_element_cnpj = wait.until(EC.presence_of_element_located((By.NAME, 'cnpj')))
            input_element_cnpj.send_keys("51097583000151")
            button_cnpj = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="button"]')))
            button_cnpj.click()
            time.sleep(5)
            current_url = driver.current_url
            print("URL:", current_url)
            expected_url = 'https://mei.receita.economia.gov.br/certificado/visualizacao'

            if current_url == expected_url:
                driver.quit()
                return {"status": "success", "govBrIdToken": "", "authorization": ""}
            else:
                print(f"A URL atual é {current_url}, não a esperada.")
                
            driver.quit()
            return {"status": "error", "message": "URL não corresponde"}
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e)}

@app.route("/", methods=["POST"])
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

@app.route("/ccmei", methods=["POST"])
def start_prenota_ccmei():
    response = Prenota.runCCMEI()
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5222, debug=True)