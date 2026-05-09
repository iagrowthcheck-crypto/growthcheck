from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from maps import buscar_negocio, obtener_resenas
from analisis import analizar_resenas
from meta import obtener_datos_pagina, obtener_posts_pagina, obtener_comentarios_recientes

load_dotenv()

app = FastAPI(title="Growth Check API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"mensaje": "Growth Check funcionando"}

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

@app.get("/facebook/{page_id}")
def get_facebook(page_id: str, token: str):
    datos = obtener_datos_pagina(page_id, token)
    posts = obtener_posts_pagina(page_id, token)
    comentarios = obtener_comentarios_recientes(page_id, token)
    return {"pagina": datos, "posts_recientes": posts, "comentarios_recientes": comentarios}