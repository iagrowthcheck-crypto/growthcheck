from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from maps import buscar_negocio, obtener_resenas
from analisis import analizar_resenas
from infra import verificar_dominio, verificar_ssl, verificar_velocidad
from database import guardar_analisis, obtener_historial, registrar_cliente, verificar_tokens, consumir_token, recargar_tokens
import anthropic
import os
import json
from typing import Optional

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
def get_analisis(nombre: str, email: Optional[str] = None):
    if email:
        tokens = verificar_tokens(email)
        if not tokens["ok"]:
            raise HTTPException(status_code=403, detail="Cliente no encontrado")
        if tokens["tokens_disponibles"] < 1:
            raise HTTPException(status_code=402, detail="Sin tokens disponibles")
    negocio = buscar_negocio(nombre)
    if "error" in negocio:
        return negocio
    resenas = obtener_resenas(negocio["place_id"])
    analisis = analizar_resenas(nombre, resenas["resenas"])
    guardar_analisis(nombre, negocio, analisis)
    if email:
        consumir_token(email, "analisis", f"Análisis de {nombre}")
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

@app.post("/consultor")
def consultor_virtual(data: dict):
    try:
        problema = data.get("problema", "")
        negocio = data.get("negocio", "mi negocio")
        email = data.get("email", None)
        if email:
            tokens = verificar_tokens(email)
            if not tokens["ok"]:
                raise HTTPException(status_code=403, detail="Cliente no encontrado")
            if tokens["tokens_disponibles"] < 1:
                raise HTTPException(status_code=402, detail="Sin tokens disponibles")
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
        resp = json.loads(resultado.strip())
        if email:
            consumir_token(email, "consultor", f"Consulta sobre: {problema[:50]}")
            tokens_actualizados = verificar_tokens(email)
            resp["tokens_restantes"] = tokens_actualizados.get("tokens_disponibles", 0)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}

@app.post("/cliente/registrar")
def registrar(data: dict):
    email = data.get("email")
    nombre = data.get("nombre", "")
    plan = data.get("plan", "basico")
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")
    return registrar_cliente(email, nombre, plan)

@app.get("/cliente/tokens")
def get_tokens(email: str):
    return verificar_tokens(email)

@app.post("/cliente/recargar")
def recargar(data: dict):
    email = data.get("email")
    cantidad = data.get("cantidad", 100)
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")
    return recargar_tokens(email, cantidad)

@app.post("/webhook/wix")
def webhook_wix(data: dict):
    try:
        email = data.get("email") or data.get("buyerInfo", {}).get("email")
        nombre = data.get("nombre") or data.get("buyerInfo", {}).get("firstName", "")
        plan = data.get("plan", "basico")
        if email:
            resultado = registrar_cliente(email, nombre, plan)
            if not resultado["ok"]:
                recargar_tokens(email, 100)
            return {"ok": True, "mensaje": "Cliente registrado y tokens asignados"}
        return {"ok": False, "error": "Email no encontrado en webhook"}
    except Exception as e:
        return {"ok": False, "error": str(e)}