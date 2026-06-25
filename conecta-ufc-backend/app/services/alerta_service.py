import logging
import smtplib
from email.mime.text import MIMEText
from typing import List

from app.models.oportunidade import OportunidadeDB
from app.services.keycloak_service import _criar_admin_keycloak

logger = logging.getLogger(__name__)

def enviar_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "no-reply@conectaufc.br"
    msg['To'] = to_email

    try:
        # SMTP no docker compose está rodando como "mailpit" na porta 1025
        with smtplib.SMTP("mailpit", 1025) as server:
            server.send_message(msg)
        logger.info(f"Email enviado com sucesso para {to_email}")
    except Exception as e:
        logger.error(f"Erro ao enviar email para {to_email}: {e}")

from app.services.keycloak_service import _criar_admin_keycloak

def obter_usuarios_por_tipo_oportunidade(tipo: str) -> List[dict]:
    try:
        keycloak_admin = _criar_admin_keycloak()
        users = keycloak_admin.get_users({})
        usuarios_interessados = []
        for u in users:
            attrs = u.get("attributes", {})
            op_list = attrs.get("oportunidades", [])
            if tipo in op_list:
                usuarios_interessados.append(u)
        return usuarios_interessados
    except Exception as e:
        logger.error(f"Erro ao buscar usuários no Keycloak pelo tipo de oportunidade {tipo}: {e}")
        return []

def disparar_alerta_nova_oportunidade(tipo: str, titulo: str, link: str):
    if not tipo:
        return
    
    usuarios_interessados = obter_usuarios_por_tipo_oportunidade(tipo)
    
    for usuario in usuarios_interessados:
        email = usuario.get("email")
        if email:
            assunto = f"Nova oportunidade de {tipo} na Conecta UFC!"
            corpo = (
                f"Olá {usuario.get('firstName', '')},\n\n"
                f"Uma nova oportunidade do tipo que você solicitou ({tipo}) acabou de ser publicada:\n\n"
                f"Título: {titulo}\n"
                f"Link: {link}\n\n"
                f"Não perca essa chance!"
            )
            enviar_email(email, assunto, corpo)

def alertar_oportunidades_proximas_do_fim(db):
    from datetime import datetime, timedelta
    
    agora = datetime.utcnow()
    daqui_a_3_dias = agora + timedelta(days=3)
    
    # Pega oportunidades que vencem em até 3 dias e que a data_fim seja no futuro
    oportunidades_vencendo = db.query(OportunidadeDB).filter(
        OportunidadeDB.data_fim != None,
        OportunidadeDB.data_fim >= agora,
        OportunidadeDB.data_fim <= daqui_a_3_dias
    ).all()
    
    for op in oportunidades_vencendo:
        if not op.tipo:
            continue
            
        usuarios_interessados = obter_usuarios_por_tipo_oportunidade(op.tipo)
        for usuario in usuarios_interessados:
            email = usuario.get("email")
            if email:
                assunto = f"Atenção: Oportunidade de {op.tipo} encerrando em breve!"
                corpo = (
                    f"Olá {usuario.get('firstName', '')},\n\n"
                    f"A oportunidade '{op.titulo}' do tipo {op.tipo} que pode ser do seu interesse "
                    f"encerra no dia {op.data_fim.strftime('%d/%m/%Y')}.\n\n"
                    f"Acesse agora para não perder: {op.link}\n\n"
                    f"Equipe Conecta UFC"
                )
                enviar_email(email, assunto, corpo)
