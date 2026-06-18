import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

raw_key = os.environ.get("ANTHROPIC_API_KEY", "")
clean_key = raw_key.replace("\n", "").replace("\r", "").strip()
client = anthropic.Anthropic(api_key=clean_key)

def analizar_resenas(nombre_negocio: str, resenas: list):
    texto_resenas = ""
    for r in resenas:
        texto_resenas += f"- {r['autor']} ({r['calificacion']} estrellas): {r['texto']}\n"

    mensaje = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": f"""Eres un Ingeniero Industrial y experto en reputacion digital para empresas en El Salvador.

Analiza estas resenas de {nombre_negocio} como si fueras un consultor operativo. Identifica no solo QUE esta fallando sino POR QUE y COMO arreglarlo con pasos concretos.

Responde UNICAMENTE con un objeto JSON valido, sin texto antes ni despues.

Formato exacto:
{{
  "sentimiento_general": "positivo/negativo/mixto",
  "porcentaje_positivo": 0,
  "porcentaje_negativo": 0,
  "principales_problemas": ["problema1", "problema2"],
  "principales_fortalezas": ["fortaleza1"],
  "alerta_critica": false,
  "resumen": "resumen breve del estado del negocio",
  "recomendacion": "accion concreta esta semana",
  "diagnostico_operativo": {{
    "proceso_que_falla": "nombre del proceso especifico (ej: atencion al cliente, cocina, delivery)",
    "etapa_del_fallo": "en que momento del flujo ocurre el problema",
    "causa_raiz": "por que esta pasando realmente este problema",
    "impacto_economico": "como este problema afecta los ingresos del negocio",
    "prioridad": "alta/media/baja"
  }},
  "plan_de_mejora": {{
    "semana_1": ["accion1", "accion2", "accion3"],
    "semana_2": ["accion1", "accion2"],
    "semana_3": ["accion1", "accion2"]
  }},
  "sop_sugerido": {{
    "titulo": "nombre del procedimiento",
    "objetivo": "que se quiere lograr",
    "pasos": ["paso1", "paso2", "paso3", "paso4", "paso5"],
    "responsable": "quien debe ejecutarlo",
    "frecuencia": "cada cuanto se aplica"
  }},
  "checklist_equipo": ["verificar1", "verificar2", "verificar3", "verificar4", "verificar5"]
}}

Resenas a analizar:
{texto_resenas}"""
            }
        ]
    )

    resultado = mensaje.content[0].text.strip()
    if resultado.startswith("```"):
        resultado = resultado.split("```")[1]
        if resultado.startswith("json"):
            resultado = resultado[4:]
    return json.loads(resultado.strip())