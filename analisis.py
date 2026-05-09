import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def analizar_resenas(nombre_negocio: str, resenas: list):
    texto_resenas = ""
    for r in resenas:
        texto_resenas += f"- {r['autor']} ({r['calificacion']} estrellas): {r['texto']}\n"

    mensaje = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Eres un experto en reputacion digital para empresas en El Salvador.

Analiza estas resenas de {nombre_negocio}. Responde UNICAMENTE con un objeto JSON valido, sin texto antes ni despues, sin bloques de codigo, sin explicaciones.

Formato exacto:
{{"sentimiento_general":"positivo/negativo/mixto","porcentaje_positivo":0,"porcentaje_negativo":0,"principales_problemas":["problema1","problema2"],"principales_fortalezas":["fortaleza1"],"alerta_critica":false,"resumen":"resumen breve","recomendacion":"accion concreta esta semana"}}

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