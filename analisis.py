import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def analizar_reseñas(nombre_negocio: str, reseñas: list):
    texto_reseñas = ""
    for r in reseñas:
        texto_reseñas += f"- {r['autor']} ({r['calificacion']} estrellas): {r['texto']}\n"

    mensaje = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Eres un experto en reputación digital para empresas en El Salvador.

Analiza estas reseñas de {nombre_negocio}. Responde ÚNICAMENTE con un objeto JSON válido, sin texto antes ni después, sin bloques de código, sin explicaciones.

Formato exacto:
{{"sentimiento_general":"positivo/negativo/mixto","porcentaje_positivo":0,"porcentaje_negativo":0,"principales_problemas":["problema1","problema2"],"principales_fortalezas":["fortaleza1"],"alerta_critica":false,"resumen":"resumen breve","recomendacion":"acción concreta esta semana"}}

Reseñas a analizar:
{texto_reseñas}"""
            }
        ]
    )

    resultado = mensaje.content[0].text.strip()
    
    # Limpiar si viene con bloques de código
    if resultado.startswith("```"):
        resultado = resultado.split("```")[1]
        if resultado.startswith("json"):
            resultado = resultado[4:]
    
    return json.loads(resultado.strip())