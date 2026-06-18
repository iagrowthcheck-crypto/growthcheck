from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from maps import buscar_negocio, obtener_resenas
from analisis import analizar_resenas
from infra import verificar_dominio, verificar_ssl, verificar_velocidad
from database import guardar_analisis, obtener_historial
import anthropic
import os
import json

load_dotenv()

raw_key = os.environ.get("ANTHROPIC_API_KEY", "")
clean_key = raw_key.replace("\n", "").replace("\r", "").strip()
client = anthropic.Anthropic(api_key=clean_key)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"ok": True}

@app.get("/negocio/{nombre}")
def get_negocio(nombre: str):
    return buscar_negocio(nombre)

@app.get("/analisis/{nombre}")
def get_analisis(nombre: str):
    negocio = buscar_negocio(nombre)
    if "error" in negocio:
        return negocio
    resenas = obtener_resenas(negocio["place_id"])
    analisis = analizar_resenas(nombre, resenas["resenas"])
    guardar_analisis(nombre, negocio, analisis)
    return {"negocio": negocio, "analisis": analisis}

@app.get("/historial/{nombre}")
def get_historial(nombre: str):
    return obtener_historial(nombre)

@app.get("/test-db")
def test_db():
    try:
        from database import get_conn
        conn = get_conn()
        conn.close()
        return {"db_ok": True, "conectado": True}
    except Exception as e:
        return {"db_ok": False, "error": str(e)}

@app.get("/dominio/{dominio}")
def get_dominio(dominio: str):
    return verificar_dominio(dominio)

@app.get("/ssl/{dominio}")
def get_ssl(dominio: str):
    return verificar_ssl(dominio)

@app.get("/velocidad")
def get_velocidad(url: str):
    return verificar_velocidad(url)

@app.get("/score/{nombre}")
def get_score(nombre: str):
    try:
        negocio = buscar_negocio(nombre)
        if "error" in negocio:
            return negocio
        resenas = obtener_resenas(negocio["place_id"])
        analisis = analizar_resenas(nombre, resenas["resenas"])
        ssl = verificar_ssl(nombre)
        dominio = verificar_dominio(nombre)
        rating = negocio.get("rating", 0)
        score_reputacion = min(100, int(rating * 20))
        positivo = analisis.get("porcentaje_positivo", 50)
        score_atencion = positivo
        ssl_ok = ssl.get("ssl_valido", False)
        dias_ssl = ssl.get("dias_restantes", 0) or 0
        score_digital = 100 if ssl_ok and dias_ssl > 30 else 50 if ssl_ok else 20
        score_general = int((score_reputacion + score_atencion + score_digital) / 3)
        historial = obtener_historial(nombre)
        score_anterior = None
        if len(historial) > 1:
            h = historial[1]
            pos_ant = h.get("porcentaje_positivo", 50)
            score_anterior = int((score_reputacion + pos_ant + score_digital) / 3)
        return {
            "scores": {
                "reputacion": score_reputacion,
                "digital": score_digital,
                "atencion_cliente": score_atencion,
                "legal": 95,
                "redes_sociales": 70,
                "general": score_general
            },
            "evolucion": {
                "anterior": score_anterior,
                "actual": score_general,
                "diferencia": score_general - score_anterior if score_anterior else None
            },
            "alertas": {
                "ssl_vence_pronto": dias_ssl < 30 if ssl_ok else True,
                "dominio_vence_pronto": dominio.get("alerta", False),
                "alerta_critica_reputacion": analisis.get("alerta_critica", False)
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/consultor")
def consultor_virtual(data: dict):
    try:
        problema = data.get("problema", "")
        negocio = data.get("negocio", "mi negocio")
        mensaje = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": f"""Eres un consultor experto en operaciones y reputacion empresarial para negocios en El Salvador.

El dueno de {negocio} tiene este problema:
"{problema}"

Responde UNICAMENTE con JSON valido:
{{
  "diagnostico": "que esta pasando realmente en 2-3 lineas",
  "causa_probable": "por que esta pasando esto",
  "acciones": [
    "accion concreta 1 para esta semana",
    "accion concreta 2",
    "accion concreta 3"
  ],
  "checklist": [
    "verificar que...",
    "confirmar que...",
    "revisar que...",
    "asegurar que..."
  ],
  "tiempo_estimado": "cuanto tiempo toma resolver esto",
  "prioridad": "alta/media/baja"
}}"""
            }]
        )
        resultado = mensaje.content[0].text.strip()
        if resultado.startswith("```"):
            resultado = resultado.split("```")[1]
            if resultado.startswith("json"):
                resultado = resultado[4:]
        return json.loads(resultado.strip())
    except Exception as e:
        return {"error": str(e)}