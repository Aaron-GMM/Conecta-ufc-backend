from sqlalchemy.orm import Session, joinedload

from app.models.oportunidade import OportunidadeDB, ResultadoDB

MENSAGEM_INFORMACAO_INDISPONIVEL = (
    "não foi possível coletar essa informação, confira no edital para qualquer dúvida"
)


def informacao_ou_mensagem(objeto, campo: str):
    try:
        valor = getattr(objeto, campo)
    except Exception:
        return MENSAGEM_INFORMACAO_INDISPONIVEL

    if valor is None:
        return MENSAGEM_INFORMACAO_INDISPONIVEL

    if isinstance(valor, str) and not valor.strip():
        return MENSAGEM_INFORMACAO_INDISPONIVEL

    return valor


def resultado_response(resultado: ResultadoDB) -> dict:
    return {
        "id": resultado.id,
        "titulo": informacao_ou_mensagem(resultado, "titulo"),
        "link": informacao_ou_mensagem(resultado, "link"),
        "data_publicacao": informacao_ou_mensagem(resultado, "data_publicacao"),
    }


def oportunidade_response(oportunidade: OportunidadeDB) -> dict:
    try:
        resultados = oportunidade.resultados or []
    except Exception:
        resultados = []

    return {
        "id": oportunidade.id,
        "titulo": informacao_ou_mensagem(oportunidade, "titulo"),
        "origem": informacao_ou_mensagem(oportunidade, "origem"),
        "tipo": informacao_ou_mensagem(oportunidade, "tipo"),
        "link": informacao_ou_mensagem(oportunidade, "link"),
        "data_inicio": informacao_ou_mensagem(oportunidade, "data_inicio"),
        "data_fim": informacao_ou_mensagem(oportunidade, "data_fim"),
        "remuneracao": informacao_ou_mensagem(oportunidade, "remuneracao"),
        "vagas": informacao_ou_mensagem(oportunidade, "vagas"),
        "data_criacao": informacao_ou_mensagem(oportunidade, "data_criacao"),
        "resultados": [resultado_response(resultado) for resultado in resultados],
    }


def _listar_oportunidades_com_ordenacao(db: Session, *criterios_ordenacao) -> list[dict]:
    oportunidades = (
        db.query(OportunidadeDB)
        .options(joinedload(OportunidadeDB.resultados))
        .order_by(*criterios_ordenacao)
        .all()
    )

    return [oportunidade_response(oportunidade) for oportunidade in oportunidades]


def listar_oportunidades_ordenadas(db: Session) -> list[dict]:
    return _listar_oportunidades_com_ordenacao(
        db,
        OportunidadeDB.data_fim.asc().nulls_last(),
    )


