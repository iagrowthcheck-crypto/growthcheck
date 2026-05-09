from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from maps import buscar_negocio, obtener_resenas
from analisis import analizar_resenas

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
    return {"negocio": negocio, "analisis": analisis}