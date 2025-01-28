import requests
import ultils
from urllib.parse import quote
from bs4 import BeautifulSoup
from datetime import datetime
import base64

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
