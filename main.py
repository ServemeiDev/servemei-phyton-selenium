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
import requests
import ultils
from urllib.parse import quote
from bs4 import BeautifulSoup
import base64
from das import post_emissao, get_data_atual, gerar_das, apurar_das, imprimir_das
from dasn import get_csrf_token_dasn, get_second_csrf_token_dasn, fetch_value_dasn, send_dasn, fetch_receipt_pdf, fetch_darf, fetch_das_execao_pdf, fetch_notificacao



app = Flask(__name__)


class WebScraper:
    @staticmethod
    def run(cnpj, ano, receita_servico, receita_comercio, informacao_empregado):
        options = udc.ChromeOptions()
        options.headless = False
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
 
        driver = udc.Chrome(use_subprocess=False, options=options)
      
        
        try:
            url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Identificacao'
            driver.get(url)
            time.sleep(2)         
            input_element = driver.find_element(By.CSS_SELECTOR, "#identificacao-cnpj")
            input_element.click()
            time.sleep(2)
            for char in cnpj:
                input_element.send_keys(char)
                time.sleep(0.1)
    
            time.sleep(2) 
            continuar_button = driver.find_element(By.CSS_SELECTOR, "#identificacao-continuar")     
            time.sleep(2) 
            continuar_button.click()

            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/'
            WebDriverWait(driver, 20).until(EC.url_to_be(expected_url))
            cookies = driver.get_cookies()
            token = get_csrf_token_dasn(cookies)
            token2 = get_second_csrf_token_dasn(token, ano, cookies)
            token3 = fetch_value_dasn(cookies, receita_comercio, receita_servico, informacao_empregado, token2)
            token4 = send_dasn(token3, cookies)
            pdf = fetch_receipt_pdf(cookies)
            pdfExcessao = fetch_das_execao_pdf(cookies) or ""
            pdfDarf = fetch_darf(cookies) or ""
            pdfNotificacao = fetch_notificacao(cookies) or ""

            result = {
                "pdfExcessao": pdfExcessao,
                "pdfDarf": pdfDarf,
                "pdf": pdf,
                "pdfNotificacao": pdfNotificacao
            }

            driver.quit()
            return result
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e)}

    @staticmethod
    def runDas(cnpj, ano, isApuration):
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
            url = f'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao'
            driver.get(url)
               
            input_element = driver.find_element(By.CSS_SELECTOR, "#cnpj")
            input_element.click()
          
            for char in cnpj:
                input_element.send_keys(char)
                time.sleep(0)
            time.sleep(2)
            continuar_button = WebDriverWait(driver, 0).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#continuar")))
            continuar_button.click()
            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Home/Inicio'
            WebDriverWait(driver, 20).until(EC.url_to_be(expected_url))
            cookies = driver.get_cookies()
            if not cookies:
                return {"status": "error", "message": "No cookies found"}
            
            driver.quit()
            
            token = post_emissao(cookies, ano)

            if "mensagem" in token and token["mensagem"]:
                return {"status": "error", "message": token["mensagem"]}

            if not token:
                return {"status": "error", "message": "Erro ao obter o token CSRF"}
            
            if isApuration:
                apurar = apurar_das(ano, cookies)
                if apurar.strip('"') != "NO":
                    return {"status": "error", "message": apurar}
                
            resultados = [] 

            for mes in range(1, 13): 
                mes_str = f"{mes:02d}" 
                gerar = gerar_das(cookies, token, ano, mes_str)
                if "mensagem" in gerar and gerar["mensagem"] and gerar["mensagem"] != "Os documentos (DAS) foram gerados com sucesso!":
                    resultados.append({
                    "mes": f"{ano}{mes:02d}",
                    "message": gerar["mensagem"],
                    })
                else:

                    imprimir = imprimir_das(cookies)

                    resultados.append({
                        "mes": f"{ano}{mes:02d}",
                        "response_data": imprimir,
                    })

                logging.info(f"Processado mês {mes_str}")

            return {"status": "success", "data": resultados}
          
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e), "cookies": []}

@app.route("/dasn", methods=["POST"])
def start_prenota():
    data = request.get_json()
    cnpj = data.get("cnpj")
    ano = data.get("ano")
    receita_servico = data.get("receita_servico")
    receita_comercio = data.get("receita_comercio")
    informacao_empregado = data.get("informacao_empregado")
    
    required_params = {
        "cnpj": cnpj,
        "ano": ano,
        "receita_servico": receita_servico,
        "receita_comercio": receita_comercio,
    }


    missing_params = [key for key, value in required_params.items() if not value]

    if "informacao_empregado" not in data:
        missing_params.append("informacao_empregado")


    if missing_params:
        return jsonify({
            "status": "error",
            "message": f"The following parameter(s) are required: {', '.join(missing_params)}"
        }), 400

    response = WebScraper.run(cnpj, ano, receita_servico, receita_comercio, informacao_empregado)
    return jsonify(response)

@app.route("/das", methods=["POST"])
def start_prenota_das():
   
    data = request.get_json()
    cnpj = data.get("cnpj")
    ano = data.get("ano")
    isApuration = data.get("isApuration")
 
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400

   
    if not ano:
        return jsonify({"status": "error", "message": "Ano is required"}), 400
    
    if isApuration is None or not isinstance(isApuration, bool):
        return jsonify({"status": "error", "message": "isApuration must be a boolean"}), 400

      
    response = WebScraper.runDas(cnpj, ano, isApuration)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)