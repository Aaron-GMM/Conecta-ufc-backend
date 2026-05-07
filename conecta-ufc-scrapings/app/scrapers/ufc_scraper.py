# app/scrapers/ufc_scraper.py
import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper


class UfcScraper(BaseScraper):


    def __init__(self):
        super().__init__()
        self.url = "https://www.quixada.ufc.br/bolsas/"
        self.origem = "UFC-Quixadá"

    def _extrair_datas(self, texto: str):
        """
        Usa Regex para encontrar padrões como 'de 02 a 05 de março de 2026'
        e retorna objetos datetime correspondentes.
        """
        if not texto:
            return None, None

        texto = texto.lower()

        padrao = r"de\s+(\d{1,2})\s+a\s+(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})"
        match = re.search(padrao, texto)

        if match:
            try:
                dia_inicio = int(match.group(1))
                dia_fim = int(match.group(2))
                mes_str = match.group(3)
                ano = int(match.group(4))

                mes = self.MESES.get(mes_str)
                if mes:
                    data_inicio = datetime(ano, mes, dia_inicio)
                    data_fim = datetime(ano, mes, dia_fim)
                    return data_inicio, data_fim
            except Exception as e:
                self.logger.warning(f"Erro ao converter datas com regex: {e}")

        return None, None

    def run(self):
        self.logger.info(f"Iniciando requisição para: {self.url}")
        html_content = self.fetch_html(self.url)

        if not html_content:
            self.logger.error("Falha ao obter o HTML da UFC. Abortando extração.")
            return []

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
            if not conteudo:
                continue

            listas_links = conteudo.find_all('ul')

            for ul in listas_links:
                titulo_vaga = "Título não encontrado"
                tag_anterior = ul.find_previous_sibling(['p', 'div', 'strong', 'h4'])

                texto_busca = ul.get_text(separator=' ')
                if tag_anterior:
                    titulo_vaga = tag_anterior.get_text(strip=True)
                    texto_busca += f" {tag_anterior.get_text(separator=' ')}"

                # Tenta extrair as datas do bloco de texto
                data_inicio, data_fim = self._extrair_datas(texto_busca)

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
                    vaga = {
                        "titulo": titulo_vaga,
                        "origem": self.origem,
                        "tipo": categoria_geral,
                        "link": link_edital,
                        "data_inicio": data_inicio,  # Agora mapeado!
                        "data_fim": data_fim,  # Agora mapeado!
                        "resultados": links_adicionais
                    }
                    oportunidades.append(vaga)

        self.logger.info(f"Total de vagas extraídas: {len(oportunidades)}")
        return oportunidades