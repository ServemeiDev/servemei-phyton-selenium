
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
import pdfkit


app = Flask(__name__)
config = pdfkit.configuration(wkhtmltopdf=r'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe') 
class WebScraper:
    @staticmethod
    def getCardCnpj(cnpj, hcapcha):
        url = 'https://solucoes.receita.fazenda.gov.br/servicos/cnpjreva/valida_recaptcha.asp'
        try:
            session = requests.Session()
            session.get(url)
            cookies = session.cookies
            cookie_list = [f"{cookie.name}={cookie.value}" for cookie in cookies]
            cookie_joined = "; ".join(cookie_list)
            data = {
                'origem': 'comprovante',
                'cnpj': cnpj,  
                'h-captcha-response': hcapcha,  
                'search_type': 'cnpj'
            }

            cookies = {
                'Cookie': cookie_joined  
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded', 
            }

            response = requests.post(url, data=data, headers=headers, cookies=cookies)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.select_one('#principal table')
            if not table:
                return {"status": "error", "data": "Tabela não encontrada no HTML"}
            table_html = str(table).replace(
				'src="images/brasao2.gif"', 
				'src="https://solucoes.receita.fazenda.gov.br/servicos/cnpjreva/images/brasao2.gif"'
			)
			
            pdf_bytes = pdfkit.from_string(f'<html><head><meta charset="UTF-8"></head><body>{table_html}</body></html>' , False ,options={ 
				
			}, configuration=config) 
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return {"status": "success", "data": pdf_base64}
    
        except Exception as error:
            print(f"Erro ao realizar o GET: {error}")
            return {"status": "error", "data": "", "message": str(error)}

    @staticmethod
    def run(cnpj, ano, receita_servico, receita_comercio, informacao_empregado):
        options = udc.ChromeOptions()
        options.headless = False
     
        options.binary_location = 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu ")
        options.add_argument("--no-sandbox")
        driver = udc.Chrome(options=options, version_main=132)  
    
    
        try:
            url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Identificacao'
            driver.get(url)
            time.sleep(2)         
            input_element = driver.find_element(By.CSS_SELECTOR, "#identificacao-cnpj")
            input_element.click()
            time.sleep(2)
            for char in cnpj:
                input_element.send_keys(char)
                time.sleep(0)
    
            time.sleep(2) 
            continuar_button = driver.find_element(By.CSS_SELECTOR, "#identificacao-continuar")     
            time.sleep(2) 
            continuar_button.click()

            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/'
            WebDriverWait(driver, 20).until(EC.url_to_be(expected_url))
            cookies = driver.get_cookies()
            if not cookies:
                return {"status": "error", "message": "No cookies found"}
            
            driver.quit()
            token = get_csrf_token_dasn(cookies)
            if not token:
                return {"status": "error", "message": "Erro ao obter o token CSRF"}
            token2 = get_second_csrf_token_dasn(token, ano, cookies)
            if not token2:
                return {"status": "error", "message": "Erro ao obter o segundo token CSRF"}
            token3 = fetch_value_dasn(cookies, receita_comercio, receita_servico, informacao_empregado, token2)

            if "messageError" in token3 and token3["messageError"]:
                return {"status": "error", "message": "Erro na validação dos dados da DASN"}
            
            send_dasn(token3, cookies)
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
        options.headless = False
        options.binary_location = 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'--user-agent={user_agent}')
        driver = udc.Chrome(use_subprocess=True, options=options,  version_main=132 )
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
        
        
    @staticmethod
    def mlink(urlLink, site, url_generation_link):
        options = udc.ChromeOptions()
        options.headless = True
     
        options.binary_location = 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu ")
        options.add_argument("--no-sandbox")
        driver = udc.Chrome(options=options, version_main=132)  

        try:
            if site == 'ml':
                url = f'{urlLink}'
                driver.get(url)
                WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.andes-button.andes-button--large.andes-button--loud"))
                )
                ver_produto_button = driver.find_element(By.CSS_SELECTOR, "a.andes-button.andes-button--large.andes-button--loud")
                product_url = ver_produto_button.get_attribute('href')
                driver.quit()
                if product_url:
                            cookie = '_csrf=cilK0cT_vvnbpTSucD7sieFS; main_domain=; main_attributes=; categories=; backend_dejavu_info=j%3A%7B%7D; cp=49142886%7C1726523058556; c_ui-navigation=6.6.92; navigation_items=MLB4109790594%7C24012025211132-MLB3952575247%7C18012025211738%7CMLB32368926%7CMLB32368920-MLB3562113013%7C16122024002939%7CMLB28718265%7CMLB28718264-MLB3814147912%7C12112024123107%7CMLB24402074%7CMLB24402056-MLB3659444039%7C16102024192620%7CMLB29219683%7CMLB29219682; _d2id=9a7e608c-eef0-44b7-b3ed-46a5790a8bfb; orgnickp=PSYSALDANHA; ftid=sqOJLELbmikD8RkrgQ9QmTb5RctwuGoh-1736983166365; ssid=ghy-012609-Ux1SZqIrQXvqq8rupqNs43bRxhQ62X-__-155183551-__-1832507386050--RRR_0-RRR_0; orguserid=d0999907H990; orguseridp=155183551; x-meli-session-id=armor.3d84e51c695c7982e4f0bc0bb42262c462ce8f89baa17fcde64049416c3eb95ca24daadcf50279bf19e5fc9ac1eaab960665ae0cb4e3cb171ff4f5aac38d5a087fdc78b9cb73e73a4bca9c328ee428f6e5a8db8953a9dd03f2f65d42048e88fd.8f1f9dbbd441d2bf95d188068a2d2a1a; cookiesPreferencesLoggedFallback=%7B%22userId%22%3A155183551%2C%22categories%22%3A%7B%22advertising%22%3Atrue%2C%22functionality%22%3Anull%2C%22performance%22%3Anull%2C%22traceability%22%3Anull%7D%7D; hide-cookie-banner_155183551=COOKIE_PREFERENCES_ALREADY_SET; tooltips-configuration={"gift_registry_tooltip":{"view_cnt":1,"close_cnt":1,"view_time":1737899570,"close_time":1737899570}}; category=MLB31447; LAST_SEARCH=daily%20t%20shirt%20insiderr; last_query=daily%20t%20shirt%20insiderr; _mldataSessionId=cabb9d70-8ebb-47ea-185b-8f8c12cb5744; cookiesPreferencesLogged=%7B%22userId%22%3A155183551%2C%22categories%22%3A%7B%22advertising%22%3Atrue%2C%22functionality%22%3Anull%2C%22performance%22%3Anull%2C%22traceability%22%3Anull%7D%7D'
                            body_data = {
                                "urls": [product_url],  
                                "tag": "psysaldanha" 
                            }
                    
                            headers = {
                                "Content-Type": "application/json", 
                                "x-csrf-token": "pOnsEYqH-z-GUKx9cafz9lYmObHzV_QYQht0", 
                                "cookie": cookie, 
                            }
                            urlGenerationLink = f"{url_generation_link}"
                            session = requests.Session()
                            response = session.post(urlGenerationLink, json=body_data, headers=headers)
                            response.raise_for_status()
                            if response.status_code == 200:
                                return response.json()
                            else:
                                return {"status": "error", "message": "Erro na requisição", "details": response.text}

                return response.text
            if site == "sp":
                url = f'{urlLink}'
                driver.get(url)
                time.sleep(1)
                second_url = driver.current_url
                driver.quit()
                return {"url": second_url}
        except Exception as e:
            logging.error(f"Exception: {e}")
            driver.quit()
            return {"status": "error", "message": str(e)}

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
        
@app.route("/card_cnpj", methods=["POST"])
def start_prenota_card():

    data = request.get_json()
    cnpj = data.get("cnpj")
    hcapcha = data.get("hcapcha")
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400
    
    if not hcapcha:
        return jsonify({"status": "error", "message": "hcapcha is required"}), 400

    response = WebScraper.getCardCnpj(cnpj, hcapcha)
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

@app.route("/ml", methods=["POST"])
def start_prenota_ml():
    data = request.get_json()
    urlLink = data.get("url")
    site = data.get("site")
    url_generation_link = data.get("url_generation_link")

    if not urlLink:
        return jsonify({"status": "error", "message": "URL is required"}), 400
    
    if not site:
         return jsonify({"status": "error", "message": "Site is required"}), 400
    
    if not url_generation_link:
        return jsonify({"status": "error", "message": "url_generation_link is required"}), 400
    
    response = WebScraper.mlink(urlLink, site, url_generation_link)
    return jsonify(response)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)