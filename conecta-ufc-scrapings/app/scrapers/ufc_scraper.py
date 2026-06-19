# app/scrapers/ufc_scraper.py
import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.pdf_parser import PdfParser


class UfcScraper(BaseScraper):


    def __init__(self):
        super().__init__()
        self.url = "https://www.quixada.ufc.br/bolsas/"
        self.origem = "UFC-Quixadá"
        self.pdf_parser = PdfParser()  # Instancia o parser

    def _extrair_datas(self, texto: str):
        """
        Usa Regex para encontrar padrões de datas no HTML.
        """
        if not texto:
            return None, None

        texto = texto.lower()

        # Padrão A: de 02 a 05 de março de 2026 | entre 02 e 05 de março de 2026
        padrao_simples = r"(?:de|entre)\s+(\d{1,2})\s+(?:a|e|até)\s+(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})"
        match_simples = re.search(padrao_simples, texto)

        if match_simples:
            try:
                dia_inicio = int(match_simples.group(1))
                dia_fim = int(match_simples.group(2))
                mes_str = match_simples.group(3)
                ano = int(match_simples.group(4))

                meses = {"janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
                mes = meses.get(mes_str)
                if mes:
                    data_inicio = datetime(ano, mes, dia_inicio)
                    data_fim = datetime(ano, mes, dia_fim)
                    return data_inicio, data_fim
            except Exception:
                pass
        
        # Padrão B: 25/02/2026 a 03/03/2026
        padrao_curto = r"(\d{2}/\d{2}(?:/\d{4})?)\s*(?:a|até|e|-)\s*(\d{2}/\d{2}/\d{4})"
        match_curto = re.search(padrao_curto, texto)
        if match_curto:
            try:
                d_inicio_str = match_curto.group(1)
                d_fim_str = match_curto.group(2)
                ano_atual = datetime.now().year
                if len(d_inicio_str) <= 5:
                    d_inicio_str += f"/{d_fim_str[-4:]}"
                
                data_inicio = datetime.strptime(d_inicio_str, "%d/%m/%Y")
                data_fim = datetime.strptime(d_fim_str, "%d/%m/%Y")
                return data_inicio, data_fim
            except ValueError:
                pass

        return None, None

    def run(self):
        self.logger.info(f"Iniciando requisição para: {self.url}")
        html_content = self.fetch_html(self.url)
        if not html_content: return []
        return self.parse_html(html_content)

    def parse_html(self, html_content):
        self.logger.info("Iniciando o parsing do HTML da UFC...")
        soup = BeautifulSoup(html_content, 'lxml')
        oportunidades = []

        blocos_sanfona = soup.find_all('article', class_='hrf-entry')

        for bloco in blocos_sanfona:
            tag_categoria = bloco.find('h3', class_='hrf-title')
            categoria_geral = tag_categoria.text.strip() if tag_categoria else "Sem Categoria"

            conteudo = bloco.find('div', class_='hrf-content')
            if not conteudo: continue

            listas_links = conteudo.find_all('ul')

            for ul in listas_links:
                titulo_vaga = "Título não encontrado"
                tag_anterior = ul.find_previous_sibling(['p', 'div', 'strong', 'h4'])
                texto_busca = ul.get_text(separator=' ')
                if tag_anterior:
                    titulo_vaga = tag_anterior.get_text(strip=True)
                    texto_busca += f" {tag_anterior.get_text(separator=' ')}"

                data_inicio_html, data_fim_html = self._extrair_datas(texto_busca)
                links_adicionais = []
                link_edital = None

                for a in ul.find_all('a'):
                    texto_link = a.get_text(strip=True)
                    href = a.get('href')
                    if any(palavra in texto_link.lower() for palavra in ['edital', 'seleção', 'chamada']):
                        link_edital = href
                    else:
                        links_adicionais.append({"titulo": texto_link, "link": href})

                if link_edital:
                    # EXTRAÇÃO PDF
                    dados_pdf = self.pdf_parser.extrair_dados(link_edital, titulo_vaga)

                    vaga = {
                        "titulo": titulo_vaga,
                        "origem": self.origem,
                        "tipo": self.normalizar_tipo(categoria_geral, titulo_vaga),
                        "link": link_edital,
                        "data_inicio": data_inicio_html or dados_pdf.get("data_inicio"),
                        "data_fim": data_fim_html or dados_pdf.get("data_fim"),
                        "remuneracao": dados_pdf.get("remuneracao"),
                        "vagas": dados_pdf.get("vagas"),
                        "coordenador": dados_pdf.get("coordenador"),
                        "descricao": dados_pdf.get("descricao"),
                        "resultados": links_adicionais
                    }
                    oportunidades.append(vaga)

        self.logger.info(f"Total de vagas extraídas: {len(oportunidades)}")
        return oportunidades