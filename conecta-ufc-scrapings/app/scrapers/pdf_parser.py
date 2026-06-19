# app/scrapers/pdf_parser.py
import io
import re
import logging
import requests
import urllib3
import pdfplumber
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PdfParser:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        self.meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
            "outubro": 10, "novembro": 11, "dezembro": 12
        }

        # 1. REMUNERAÇÃO: Agora aceita "R$ 400" ou "R$ 400,00"
        self.re_remuneracao = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)", re.IGNORECASE)

        # 2. VAGAS: Expandido para monitor, monitores, bolsista, bolsistas
        self.re_vagas = re.compile(r"(\d+)\s*(?:vaga[s]?|bolsa[s]?|monitor(?:es)?|bolsista[s]?)", re.IGNORECASE)

        # 3. DATAS:
        # Padrão A: "25 de fevereiro de 2026 a 04 de março de 2026" OU "entre 25 de fevereiro e 04 de março"
        self.re_data_extenso = re.compile(
            r"(\d{1,2})\s*(?:de\s+([a-zç]+)\s+de\s+\d{4})?\s*(?:a|até|e)\s*(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})",
            re.IGNORECASE
        )
        # Padrão B: Tabela/Curto "25/02/2026 a 03/03/2026" ou "entre os dias 25/02 e 03/03"
        self.re_data_curta = re.compile(
            r"(?:inscrições|envio|dias|período).*?(?:(\d{2}/\d{2}(?:/\d{4})?)\s*(?:a|até|e)\s*)?(\d{2}/\d{2}/\d{4})",
            re.IGNORECASE
        )

    def _converter_str_para_float(self, valor_str: str) -> float:
        valor_limpo = valor_str.replace('.', '').replace(',', '.')
        try:
            return float(valor_limpo)
        except ValueError:
            return 0.0

    def _obter_bytes_do_pdf(self, url: str) -> io.BytesIO:
        try:
            if '1drv.ms' in url or 'onedrive.live' in url:
                self.logger.warning("Links do OneDrive são bloqueados. Ignorando.")
                return None

            resposta = requests.get(url, headers=self.headers, verify=False, timeout=15)
            resposta.raise_for_status()
            content_type = resposta.headers.get('Content-Type', '').lower()

            if 'application/pdf' in content_type or url.lower().split('?')[0].endswith('.pdf'):
                return io.BytesIO(resposta.content)

            elif 'text/html' in content_type:
                soup = BeautifulSoup(resposta.text, 'lxml')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '.pdf' in href.lower():
                        url_pdf = urljoin(url, href)
                        resp_pdf = requests.get(url_pdf, headers=self.headers, verify=False, timeout=15)
                        if 'application/pdf' in resp_pdf.headers.get('Content-Type', '').lower() or \
                                url_pdf.lower().split('?')[0].endswith('.pdf'):
                            return io.BytesIO(resp_pdf.content)

                    drive_match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', href)
                    if drive_match:
                        file_id = drive_match.group(1)
                        url_download = f"https://drive.google.com/uc?export=download&id={file_id}"
                        resp_drive = requests.get(url_download, verify=False, timeout=15)
                        return io.BytesIO(resp_drive.content)
            return None
        except Exception as e:
            self.logger.error(f"Erro ao baixar/resolver PDF de {url}: {e}")
            return None

    def extrair_dados(self, link: str, titulo: str) -> dict:
        if "resultado" in titulo.lower() or "deferimento" in titulo.lower() or "aditivo" in titulo.lower():
            self.logger.info(f"Ignorando leitura de PDF de Resultado/Aditivo: {titulo}")
            return {"remuneracao": None, "vagas": None, "data_inicio": None, "data_fim": None}

        pdf_bytes = self._obter_bytes_do_pdf(link)
        if not pdf_bytes:
            return {"remuneracao": None, "vagas": None, "data_inicio": None, "data_fim": None}

        texto_completo = ""
        try:
            with pdfplumber.open(pdf_bytes) as pdf:
                for pagina in pdf.pages:
                    texto_extraido = pagina.extract_text()
                    if texto_extraido:
                        texto_completo += texto_extraido + "\n"
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF em memória: {e}")
            return {"remuneracao": None, "vagas": None, "data_inicio": None, "data_fim": None}

        dados = {
            "remuneracao": None,
            "vagas": None,
            "data_inicio": None,
            "data_fim": None,
            "coordenador": None,
            "descricao": None
        }

        # 1. Remuneração
        match_remun = self.re_remuneracao.search(texto_completo)
        if match_remun:
            dados["remuneracao"] = self._converter_str_para_float(match_remun.group(1))

        # 2. Vagas (Procura apenas no topo do documento para evitar falsos positivos)
        matches_vagas = self.re_vagas.findall(texto_completo[:2000])
        if matches_vagas:
            total_vagas = sum(int(v) for v in matches_vagas)
            dados["vagas"] = total_vagas if total_vagas > 0 else 1

        # 3. Datas (Tenta Curto/Tabela primeiro, depois Extenso)
        match_curta = self.re_data_curta.search(texto_completo)
        if match_curta:
            d_inicio_str = match_curta.group(1)
            d_fim_str = match_curta.group(2)
            ano_atual = datetime.now().year

            try:
                if d_inicio_str:
                    # Se vier só dia/mês ("25/02"), coloca o ano da data fim
                    if len(d_inicio_str) <= 5:
                        d_inicio_str += f"/{d_fim_str[-4:] if d_fim_str else ano_atual}"
                    dados["data_inicio"] = datetime.strptime(d_inicio_str, "%d/%m/%Y")

                if d_fim_str:
                    dados["data_fim"] = datetime.strptime(d_fim_str, "%d/%m/%Y")
            except ValueError:
                pass

        if not dados["data_fim"]:
            match_extenso = self.re_data_extenso.search(texto_completo)
            if match_extenso:
                try:
                    dia_inicio = int(match_extenso.group(1))
                    mes_inicio_str = match_extenso.group(2)
                    dia_fim = int(match_extenso.group(3))
                    mes_fim_str = match_extenso.group(4).lower()
                    ano = int(match_extenso.group(5))

                    mes_fim = self.meses.get(mes_fim_str)
                    mes_inicio = self.meses.get(mes_inicio_str.lower()) if mes_inicio_str else mes_fim

                    if mes_fim and mes_inicio:
                        dados["data_inicio"] = datetime(ano, mes_inicio, dia_inicio)
                        dados["data_fim"] = datetime(ano, mes_fim, dia_fim)
                except Exception:
                    pass

        # NOVO: Coordenador
        match_email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", texto_completo)
        if match_email:
            dados["coordenador"] = match_email.group(0)
        else:
            match_prof = re.search(r"(?:Coordenador[a]?|Prof(?:essor|a|\.)?)\s*[:-]?\s*([A-Z][A-Za-zÀ-ÿ\s]+)", texto_completo)
            if match_prof:
                nome_limpo = match_prof.group(1).strip()
                if len(nome_limpo) > 4:
                    dados["coordenador"] = " ".join(nome_limpo.split()[:4])
        
        # NOVO: Descrição
        # 1. Tenta achar seções específicas
        match_objeto = re.search(r"(?:DO OBJETO|1\.\s*OBJETO|1\.\s*DISPOSIÇÕES GERAIS|OBJETIVO)\s*\n*(.+?)(?=\n\n|\n\d|\Z)", texto_completo, re.IGNORECASE | re.DOTALL)
        if match_objeto and len(match_objeto.group(1).strip()) > 50:
            descricao = match_objeto.group(1).replace('\n', ' ').strip()
            dados["descricao"] = descricao[:500] + ("..." if len(descricao) > 500 else "")
        else:
            # 2. Fallback inteligente: Pega a primeira sentença longa com contexto
            texto_limpo = re.sub(r'\s+', ' ', texto_completo)
            sentencas = [s.strip() + '.' for s in texto_limpo.split('. ') if s.strip()]
            
            descricao_encontrada = ""
            for i, s in enumerate(sentencas):
                if len(s) > 100 and "EDITAL" not in s[:20].upper() and "UNIVERSIDADE" not in s[:30].upper() and "RESULTADO" not in s[:30].upper():
                    descricao_encontrada = s
                    if i + 1 < len(sentencas) and len(descricao_encontrada) < 250:
                        descricao_encontrada += ' ' + sentencas[i+1]
                    break
            
            if descricao_encontrada:
                dados["descricao"] = descricao_encontrada[:500] + ("..." if len(descricao_encontrada) > 500 else "")
            else:
                dados["descricao"] = texto_limpo[:500] + "..."

        self.logger.info(f"Dados extraídos com sucesso para '{titulo}': {dados}")
        return dados