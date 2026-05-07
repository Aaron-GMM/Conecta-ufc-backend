# app/api/routes/scraper_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.oportunidade import OportunidadeDB, ResultadoDB
from app.scrapers.fastef_scraper import FastefScraper
from app.scrapers.ufc_scraper import UfcScraper
import re

router = APIRouter(prefix="/api/scrapers", tags=["Scrapers"])

@router.post("/ufc/run")
def rodar_scraper_ufc(db: Session = Depends(get_db)):
    scraper = UfcScraper()
    dados_extraidos = scraper.run()

    salvos = 0
    duplicados = 0
    resultados_salvos = 0

    links_processados_agora = set()
    resultados_processados_agora = set()

    for item in dados_extraidos:
        link = item["link"]

        if link in links_processados_agora:
            duplicados += 1
            continue

        links_processados_agora.add(link)

        vaga_db = db.query(OportunidadeDB).filter(OportunidadeDB.link == link).first()

        if not vaga_db:
            vaga_db = OportunidadeDB(
                titulo=item["titulo"],
                origem=item["origem"],
                tipo=item["tipo"],
                link=link
            )
            db.add(vaga_db)
            db.flush()
            salvos += 1
        else:
            duplicados += 1

        # Processa os resultados
        for res in item.get("resultados", []):
            res_link = res["link"]

            if res_link in resultados_processados_agora:
                continue

            resultados_processados_agora.add(res_link)

            existe_res = db.query(ResultadoDB).filter(ResultadoDB.link == res_link).first()

            if not existe_res:
                novo_resultado = ResultadoDB(
                    titulo=res["titulo"],
                    link=res_link,
                    oportunidade_id=vaga_db.id
                )
                db.add(novo_resultado)
                resultados_salvos += 1

    db.commit()

    return {
        "status": "sucesso",
        "total_extraido": len(dados_extraidos),
        "editais_salvos": salvos,
        "resultados_salvos": resultados_salvos,
        "editais_ignorados_por_duplicidade": duplicados
    }


@router.post("/fastef/run")
def rodar_scraper_fastef(db: Session = Depends(get_db)):
    scraper = FastefScraper()
    dados_extraidos = scraper.run()

    salvos = 0
    resultados_salvos = 0
    duplicados = 0

    editais_para_salvar = []
    resultados_para_processar = []
    links_processados = set()

    # 0. Separação de Pais e Filhos
    for item in dados_extraidos:
        link = item["link"]
        if link in links_processados: continue
        links_processados.add(link)

        if "resultado" in item["titulo"].lower():
            resultados_para_processar.append(item)
        else:
            editais_para_salvar.append(item)

    for item in editais_para_salvar:
        existe = db.query(OportunidadeDB).filter(OportunidadeDB.link == item["link"]).first()
        if existe:
            duplicados += 1
            continue

        match = re.search(r'(edital\s*\d+/\d+)', item["titulo"], re.IGNORECASE)
        if match:
            padrao_edital = match.group(1).lower().replace(' ', '-').replace('/', '-')
            link_provisorio = f"pendente-{padrao_edital}"

            fantasma = db.query(OportunidadeDB).filter(OportunidadeDB.link == link_provisorio).first()
            if fantasma:
                fantasma.titulo = item["titulo"]
                fantasma.link = item["link"]
                db.flush()
                continue

        nova_vaga = OportunidadeDB(
            titulo=item["titulo"],
            origem=item["origem"],
            tipo=item["tipo"],
            link=item["link"]
        )
        db.add(nova_vaga)
        salvos += 1

    db.flush()

    for item in resultados_para_processar:
        titulo = item["titulo"]
        link = item["link"]

        match = re.search(r'(edital\s*\d+/\d+)', titulo, re.IGNORECASE)
        if match:
            padrao_edital = match.group(1)
            link_provisorio = f"pendente-{padrao_edital.lower().replace(' ', '-').replace('/', '-')}"

            vaga_pai = db.query(OportunidadeDB).filter(
                OportunidadeDB.origem == "FASTEF",
                OportunidadeDB.titulo.ilike(f"%{padrao_edital}%"),
                ~OportunidadeDB.titulo.ilike("%resultado%")
            ).first()

            if not vaga_pai:
                vaga_pai = db.query(OportunidadeDB).filter(OportunidadeDB.link == link_provisorio).first()

            if not vaga_pai:
                vaga_pai = OportunidadeDB(
                    titulo=f"{padrao_edital.upper()} (Edital Base)",
                    origem=item["origem"],
                    tipo=item["tipo"],
                    link=link_provisorio
                )
                db.add(vaga_pai)
                db.flush()
                salvos += 1

            existe_res = db.query(ResultadoDB).filter(ResultadoDB.link == link).first()
            if not existe_res:
                novo_res = ResultadoDB(
                    titulo=titulo,
                    link=link,
                    oportunidade_id=vaga_pai.id
                )
                db.add(novo_res)
                resultados_salvos += 1
        else:
            existe = db.query(OportunidadeDB).filter(OportunidadeDB.link == link).first()
            if not existe:
                nova_vaga = OportunidadeDB(
                    titulo=titulo, origem=item["origem"], tipo=item["tipo"], link=link
                )
                db.add(nova_vaga)
                salvos += 1
            else:
                duplicados += 1

    db.commit()

    return {
        "status": "sucesso",
        "total_extraido": len(dados_extraidos),
        "editais_salvos": salvos,
        "resultados_salvos": resultados_salvos,
        "ignorados_por_duplicidade": duplicados
    }