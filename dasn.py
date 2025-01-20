import requests
import ultils
from urllib.parse import quote
from bs4 import BeautifulSoup

def get_second_csrf_token_dasn(token: str, ano: int, cookies: str):
    url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Declaracao/Iniciar'
    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
       
        form_data = {
            '__RequestVerificationToken': token,
            'anoCalendarioSelecionado': str(ano),
        }
        response = session.post(url, data=form_data)
       
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

def get_csrf_token_dasn(cookies):
    url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/'
    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        response = session.post(url)
       
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

def fetch_value_dasn(cookies: str, receita_comercio: str, receita_servico: str, informacao_empregado: bool, token: str) -> dict:
    
    url_preencher = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Declaracao/Preencher"  # Substitua pela URL correta
    url_dasn_erro = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Declaracao/Erro"  # Substitua pela URL correta
           
    form_data = {
        'valorReceitaTotal': '0',
        'valorReceitaIcms': receita_comercio,
        'valorReceitaIss': receita_servico,
        'informacaoEmpregado': str(informacao_empregado).lower(),
        '__RequestVerificationToken': token,
    }
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    session = requests.Session()
    session.cookies.update(cookie_dict)
    cookie_string = "; ".join([f"{name}={value}" for name, value in cookie_dict.items()])
    
    try:
        response = session.post(url_preencher, data=form_data)
        response.raise_for_status()
       
        soup = BeautifulSoup(response.text, 'html.parser')
       
        csrf_token_input = soup.select_one('form input[name="__RequestVerificationToken"]')
        csrf_token = csrf_token_input['value'] if csrf_token_input else None

        return {'csrfToken': csrf_token}

    except requests.exceptions.RequestException as error:
        print(error.response.text)
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        response = requests.get(url_dasn_erro)
        soup = BeautifulSoup(response.content, 'html.parser')
  
        return {'messageError': response.content}

def send_dasn(token: str, cookies: str):
    url = 'https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Transmissao'
    try:
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        session = requests.Session()
        session.cookies.update(cookie_dict)
        form_data = {
            '__RequestVerificationToken': token,
        }
        response = session.post(url, data=form_data)
        if response.status_code == 200:
            return { "success": True }
        else:
            print("CSRF Token não encontrado.")
        return None
    except Exception as error:
        print(f"Erro ao realizar o POST: {error}")
        return None
