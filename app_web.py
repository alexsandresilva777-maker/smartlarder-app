import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# As permissões que definimos lá no Google Cloud (Escopos)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

def autenticar_google():
    creds = None
    # O arquivo 'token.json' armazena o seu acesso para você não ter que logar toda hora
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Se não houver credenciais válidas, pede o login no navegador
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # É AQUI que o Python lê o arquivo que você baixou!
            # Certifique-se de que o arquivo baixado se chama 'credentials.json'
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva as credenciais para o próximo uso
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)

# Para usar no seu código:
# service = autenticar_google()
# sheet = service.spreadsheets()
