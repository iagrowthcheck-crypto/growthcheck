from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from maps import buscar_negocio, obtener_resenas
from analisis import analizar_resenas
from infra import verificar_dominio, verificar_ssl, verificar_velocidad
from database import guardar_analisis, obtener_historial

load_dotenv()
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

@app.get("/dominio/{dominio}")
def get_dominio(dominio: str):
    return verificar_dominio(dominio)

@app.get("/ssl/{dominio}")
def get_ssl(dominio: str):
    return verificar_ssl(dominio)

@app.get("/velocidad")
def get_velocidad(url: str):
    return verificar_velocidad(url)
@app.get("/test-db")
def test_db():
    from database import supabase
    try:
        result = supabase.table("analisis").select("count").execute()
        return {"db_ok": True, "data": result.data}
    except Exception as e:
        return {"db_ok": False, "error": str(e)}