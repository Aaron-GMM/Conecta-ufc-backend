import requests
import logging
from typing import List
from app.schemas.oportunidade import OportunidadeSync

logger = logging.getLogger(__name__)

def link_acessivel(url: str) -> bool:
    """Verifica se a URL está bloqueada ou inacessível."""
    if not url:
        return False
    try:
        # Usamos timeout curto para não travar a sincronização
        response = requests.head(url, timeout=5, allow_redirects=True, verify=False)
        return response.status_code < 400
    except requests.RequestException:
        # Se o HEAD falhar (alguns servidores bloqueiam HEAD), tentamos GET com range pequeno
        try:
            response = requests.get(url, headers={'Range': 'bytes=0-10'}, timeout=5, verify=False)
            return response.status_code < 400
        except requests.RequestException:
            return False

def is_dado_valido(item: OportunidadeSync) -> bool:
    """
    Avalia a qualidade do dado retornado pelo scraper.
    Retorna True se for válido para ser salvo no banco, False se deve ser descartado.
    """
    if not item.titulo or item.titulo.lower() in ["sem título", "undefined", "null"]:
        logger.warning(f"Oportunidade rejeitada (Título Inválido): {item.titulo}")
        return False

    if not item.link:
        logger.warning(f"Oportunidade rejeitada (Link Vazio): {item.titulo}")
        return False

    # Checa informações vazias
    campos_vazios = 0
    if item.data_inicio is None: campos_vazios += 1
    if item.data_fim is None: campos_vazios += 1
    if item.remuneracao is None: campos_vazios += 1
    if item.vagas is None: campos_vazios += 1

    # Se todos os principais campos descritivos estiverem vazios, a utilidade é muito baixa
    if campos_vazios == 4:
        # Pode ser um edital sem formato padrão ou bloqueado. 
        # Vamos verificar se o link ao menos está acessível. Se estiver inacessível e vazio, rejeita.
        if not link_acessivel(item.link):
            logger.warning(f"Oportunidade rejeitada (Muitos vazios e link bloqueado/inacessível): {item.link}")
            return False
        
        # Opcional: mesmo se acessível, talvez não queremos se está 100% vazio, 
        # mas vamos rejeitar definitivamente se tiver muitos vazios e o link for ruim.
        # Se preferir rejeitar TUDO que for 4 campos vazios, descomente a linha abaixo:
        logger.warning(f"Oportunidade rejeitada (Sem dados de datas, vagas e remuneração): {item.link}")
        return False

    return True

def filtrar_oportunidades_qualificadas(data: List[OportunidadeSync]) -> List[OportunidadeSync]:
    """
    Filtra a lista de oportunidades, removendo as de baixa qualidade.
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    qualificados = []
    for item in data:
        if is_dado_valido(item):
            qualificados.append(item)
    return qualificados
