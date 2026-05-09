from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from maps import buscar_negocio, obtener_reseñas
from analisis import analizar_reseñas
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
    return {"mensaje": "Growth Check esta funcionando"}

@app.get("/negocio/{nombre}")
def get_negocio(nombre: str):
    return buscar_negocio(nombre)

@app.get("/resenas/{place_id}")
def get_resenas(place_id: str):
    return obtener_reseñas(place_id)

@app.get("/analisis/{nombre}")
def get_analisis(nombre: str):
    negocio = buscar_negocio(nombre)
    if "error" in negocio:
        return negocio
    resenas = obtener_reseñas(negocio["place_id"])
    analisis = analizar_reseñas(nombre, resenas["reseñas"])
    return {"negocio": negocio, "analisis": analisis}

@app.get("/facebook/{page_id}")
def get_facebook(page_id: str, token: str):
    datos = obtener_datos_pagina(page_id, token)
    posts = obtener_posts_pagina(page_id, token)
    comentarios = obtener_comentarios_recientes(page_id, token)
    return {"pagina": datos, "posts_recientes": posts, "comentarios_recientes": comentarios}