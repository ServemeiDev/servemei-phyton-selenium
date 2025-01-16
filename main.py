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

class MyHTTPAdapter(requests.adapters.HTTPAdapter):
    def send(self, request, **kwargs):
        print(f"\n[Request] {request.method} {request.url}")
        print("Headers:", request.headers)
        print("Body:", request.body)
        response = super().send(request, **kwargs)
        print(f"[Response] {response.status_code} {response.url}")
        print("Headers:", response.headers)
        print("Body:", response.text)
        return response


def get_data_atual():
    current_date = datetime.now()
    return current_date.strftime('%d/%m/%Y')

def gerar_das(cookies, token, ano, mes):
    url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao/gerarDas'   
    data = {
         "__RequestVerificationToken": token,
        'ano': str(ano),
        'pa': f"{ano}{mes}",
        'dataConsolidacao': get_data_atual(),
    }

    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        response = session.post(url, data=data)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script', string=lambda text: text and 'Notificacao.Show' in text)
            mensagens = []

            for script in scripts:
                start_index = script.string.find("','") + 2  
                end_index = script.string.find("');", start_index) 
                if start_index != -1 and end_index != -1:
                    mensagem = script.string[start_index:end_index].strip("'")
                    mensagens.append(mensagem)

            if len(mensagens) > 1:
                return {"mensagem": mensagens[1] }
            elif mensagens: 
                return {"mensagem": mensagens[0] }
            
            return response.text
        else:
            return None
    except Exception as error:
        return None


def post_emissao(cookies, ano):
    url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao'
    data = {
        'ano': str(ano)
    }
    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        response = session.post(url, data=data)
        if response.status_code == 200:
           soup = BeautifulSoup(response.text, 'html.parser')
           csrf_token = soup.find('input', {'name': '__RequestVerificationToken'})
           script = soup.find('script', string=lambda text: text and 'Notificacao.Show' in text)
           if script:
               start_index = script.string.find("','") + 2  # Localiza o início da mensagem
               end_index = script.string.find("');", start_index)  # Localiza o final da mensagem
               mensagem = script.string[start_index:end_index]
               mensagem = mensagem.strip("'")
               return { "mensagem": mensagem }
           
           if csrf_token:
               token_value = csrf_token.get('value')
               return token_value
           else:
               print("CSRF Token não encontrado.")
           return None
    except Exception as error:
        print(f"Erro ao realizar o POST: {error}")
        return None
    
def apurar_das(ano: int, cookies: str) -> dict:
    url = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Emissao/VerificaRetificacaoAutomatica" 
    form_data = {
        'ano': str(ano),
        'aliquotaDivergente': 'false',
        'valorTributoDivergente': 'false'
    }

    lista_pa = [f"{ano}{str(mes).zfill(2)}" for mes in range(1, 13)]
    form_data['listaPA'] = lista_pa

    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        response = session.post(url, data=form_data)

        if response.status_code == 200:
            return response.text
        else:
            return {"status": "error", "message": "Erro na requisição", "details": response.text}
    except requests.exceptions.RequestException as error:
        return {"status": "error", "message": str(error)}

def imprimir_das(cookies: str) -> str:
    url = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao/imprimir" 
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    session = requests.Session()
    session.cookies.update(cookie_dict)
    try:
        response = session.get(url)
        response.raise_for_status()  # Levanta um erro para status HTTP 4xx/5xx
        
        if response.status_code == 200:
            recibo_pdf = base64.b64encode(response.content).decode('utf-8')
            return recibo_pdf
        else:
            print(f"Erro na requisição GET: {response.status_code}")
            return None
    except requests.RequestException as error:
        print(f"Erro ao realizar o GET: {error}")
        return None


app = Flask(__name__)


class Prenota:
    @staticmethod
    def run(cnpj):
        options = udc.ChromeOptions()
        options.headless = False
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        ua = UserAgent()
        user_agent = ua.random
        options.add_argument(f'--user-agent={user_agent}')
        driver = udc.Chrome(use_subprocess=False, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        })
        
       
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
    
            time.sleep(5) 
            continuar_button = driver.find_element(By.CSS_SELECTOR, "#identificacao-continuar")
            continuar_button.click()
             
            time.sleep(2) 

            expected_url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/'
            WebDriverWait(driver, 20).until(EC.url_to_be(expected_url))
            cookies = driver.get_cookies()
            cokiesString = cookies_to_string(cookies)
            print(cokiesString)
            
            
             
            

            print("Cookies:", cokiesString)
            driver.quit()
            return {"status": "success", "cookies": cookies}
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

                if "mensagem" in gerar and gerar["mensagem"]:
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
    # Obtém o CNPJ do corpo da requisição
    data = request.get_json()
    cnpj = data.get("cnpj")
    print(cnpj)
    
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400

  
    Prenota.run(cnpj)
    return jsonify(response)

@app.route("/das", methods=["POST"])
def start_prenota_das():
    # Obtém o CNPJ do corpo da requisição
    data = request.get_json()
    cnpj = data.get("cnpj")
    ano = data.get("ano")
    isApuration = data.get("isApuration")
    print(cnpj)
    
    # Validação do CNPJ
    if not cnpj:
        return jsonify({"status": "error", "message": "CNPJ is required"}), 400

    # Validação do Ano
    if not ano:
        return jsonify({"status": "error", "message": "Ano is required"}), 400
    
    if isApuration is None or not isinstance(isApuration, bool):
        return jsonify({"status": "error", "message": "isApuration must be a boolean"}), 400

      
    response = Prenota.runDas(cnpj, ano, isApuration)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)