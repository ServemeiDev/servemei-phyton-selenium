
from bs4 import BeautifulSoup
import base64
import requests
from datetime import datetime

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
            return response.text
        else:
            return None
    except Exception as error:
        return None

def post_emissao(cookies):
    url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/emissao'
    data = {
        'ano': str(2023)
    }
    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        response = session.post(url, data=data)
        if response.status_code == 200:
           soup = BeautifulSoup(response.text, 'html.parser')
           csrf_token = soup.find('input', {'name': '__RequestVerificationToken'})
           if csrf_token:
                token_value = csrf_token.get('value')
                return token_value
           else:
                print("CSRF Token não encontrado.")
        else:
            print(f"Erro na requisição POST: {response.status_code}")
            return None
    except Exception as error:
        print(f"Erro ao realizar o POST: {error}")
        return None

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
