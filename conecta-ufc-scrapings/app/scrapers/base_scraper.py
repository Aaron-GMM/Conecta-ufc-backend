import requests
import logging
from time import sleep
import urllib3

# Desativa os avisos de requisição insegura (já que estamos usando verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração de Logs
logging.basicConfig(
    filename='scraper_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_html(self, url: str, retries: int = 3):
        """Tenta fazer o request com retries em caso de falha."""
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10, verify=False)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Erro ao acessar {url} (Tentativa {attempt + 1}/{retries}): {e}")
                sleep(2)
        self.logger.critical(f"Falha total ao acessar {url} após {retries} tentativas.")
        return None