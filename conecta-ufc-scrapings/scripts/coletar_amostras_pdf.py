# scripts/coletar_amostras_pdf.py
import os
import sys
import logging
import requests
import urllib3
import re
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import urljoin

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.ufc_scraper import UfcScraper
from app.scrapers.fastef_scraper import FastefScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("HelperPDF")
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler("helper_pdfs_v4.log", mode='w', encoding='utf-8')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

PASTA_AMOSTRAS = "amostras_pdf"


def setup_pasta():
    if not os.path.exists(PASTA_AMOSTRAS):
        os.makedirs(PASTA_AMOSTRAS)
        logger.info(f"Pasta '{PASTA_AMOSTRAS}' criada.")


def baixar_do_google_drive(file_id, caminho_salvamento):
    url_download = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        resposta = requests.get(url_download, verify=False, timeout=15)
        resposta.raise_for_status()
        with open(caminho_salvamento, 'wb') as f:
            f.write(resposta.content)
        logger.info(f"✅ PDF do Google Drive salvo: {caminho_salvamento}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao baixar do Google Drive (ID: {file_id}): {e}")
        return False


def buscar_e_baixar_pdfs(url_pagina: str, nome_sugerido: str):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        logger.info(f"[{nome_sugerido}] Analisando link: {url_pagina}")

        # Pula links do OneDrive pois exigem renderização de JS ou dão 403
        if '1drv.ms' in url_pagina or 'onedrive.live' in url_pagina:
            logger.warning(f"⚠️ Link do OneDrive detectado e ignorado (bloqueado p/ scrapers): {url_pagina}")
            return False

        resposta = requests.get(url_pagina, headers=headers, verify=False, timeout=15)
        resposta.raise_for_status()

        content_type = resposta.headers.get('Content-Type', '').lower()

        # CENÁRIO 1: O link já é um PDF direto (Padrão UFC)
        if 'application/pdf' in content_type or url_pagina.lower().split('?')[0].endswith('.pdf'):
            caminho = os.path.join(PASTA_AMOSTRAS, f"{nome_sugerido}_direto.pdf")
            with open(caminho, 'wb') as f:
                f.write(resposta.content)
            logger.info(f"✅ PDF direto salvo: {caminho}")
            return True

        # CENÁRIO 2: O link é uma página web (Padrão FASTEF)
        elif 'text/html' in content_type:
            soup = BeautifulSoup(resposta.text, 'lxml')

            for a in soup.find_all('a', href=True):
                href = a['href']

                # Procura link de PDF embutido
                if '.pdf' in href.lower():
                    url_real_pdf = urljoin(url_pagina, href)
                    logger.info(f"[{nome_sugerido}] Encontrado PDF embutido: {url_real_pdf}")

                    resp_pdf = requests.get(url_real_pdf, headers=headers, verify=False, timeout=15)
                    if 'application/pdf' in resp_pdf.headers.get('Content-Type', '').lower() or \
                            url_real_pdf.lower().split('?')[0].endswith('.pdf'):
                        caminho = os.path.join(PASTA_AMOSTRAS, f"{nome_sugerido}_embutido.pdf")
                        with open(caminho, 'wb') as f:
                            f.write(resp_pdf.content)
                        logger.info(f"✅ PDF embutido salvo com sucesso: {caminho}")
                        return True

                # Procura link do Google Drive
                drive_match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', href)
                if drive_match:
                    file_id = drive_match.group(1)
                    logger.info(f"[{nome_sugerido}] Encontrado link do Google Drive. ID: {file_id}")
                    caminho = os.path.join(PASTA_AMOSTRAS, f"{nome_sugerido}_gdrive.pdf")
                    return baixar_do_google_drive(file_id, caminho)

            logger.warning(f"❌ Nenhum PDF ou Google Drive encontrado na página HTLM.")
            return False

    except Exception as e:
        logger.error(f"❌ Erro ao acessar a URL: {e}")
        return False


def extrair_lote_amostras(scraper_class, nome_origem, qtd_desejada=3):
    logger.info("\n" + "=" * 50)
    logger.info(f" INICIANDO EXTRAÇÃO DE {qtd_desejada} AMOSTRAS: {nome_origem}")
    logger.info("=" * 50)

    scraper = scraper_class()
    vagas = scraper.run()
    pdfs_salvos = 0

    for vaga in vagas:
        if pdfs_salvos >= qtd_desejada:
            break

        link = vaga.get('link')
        if not link:
            continue

        nome_arquivo = f"{nome_origem}_amostra_{pdfs_salvos + 1}"
        sucesso = buscar_e_baixar_pdfs(link, nome_arquivo)

        if sucesso:
            pdfs_salvos += 1

        sleep(2)


if __name__ == "__main__":
    setup_pasta()
    # Baixando 3 de cada
    extrair_lote_amostras(UfcScraper, "UFC", qtd_desejada=3)
    extrair_lote_amostras(FastefScraper, "FASTEF", qtd_desejada=3)
    logger.info("\nFim do processo de amostragem.")