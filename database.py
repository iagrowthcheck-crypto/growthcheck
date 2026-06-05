import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def guardar_analisis(negocio: str, datos_negocio: dict, datos_analisis: dict):
    try:
        record = {
            "negocio": negocio,
            "rating": datos_negocio.get("rating"),
            "total_resenas": datos_negocio.get("total_resenas"),
            "direccion": datos_negocio.get("direccion"),
            "sentimiento": datos_analisis.get("sentimiento_general"),
            "porcentaje_positivo": datos_analisis.get("porcentaje_positivo"),
            "porcentaje_negativo": datos_analisis.get("porcentaje_negativo"),
            "alerta_critica": datos_analisis.get("alerta_critica"),
            "resumen": datos_analisis.get("resumen"),
            "recomendacion": datos_analisis.get("recomendacion"),
            "problemas": datos_analisis.get("principales_problemas"),
            "fortalezas": datos_analisis.get("principales_fortalezas")
        }
        result = supabase.table("analisis").insert(record).execute()
        return {"guardado": True}
    except Exception as e:
        return {"guardado": False, "error": str(e)}

def obtener_historial(negocio: str):
    try:
        result = supabase.table("analisis").select("*").eq("negocio", negocio).order("fecha", desc=True).execute()
        return result.data
    except Exception as e:
        return []