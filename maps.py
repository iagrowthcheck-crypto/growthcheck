import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def extraer_place_id_de_url(maps_url: str):
    """Sigue el link (incluso si es un link corto tipo share.google) y busca el place_id en la URL final."""
    try:
        response = requests.get(maps_url, allow_redirects=True, timeout=10)
        url_final = response.url

        match = re.search(r"place_id=([\w-]+)", url_final)
        if match:
            return match.group(1)

        match_cid = re.search(r"[?&]cid=(\d+)", url_final)
        if match_cid:
            return buscar_place_id_por_cid(match_cid.group(1))

        return None
    except Exception:
        return None

def buscar_place_id_por_cid(cid: str):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": f"cid:{cid}", "fields": "place_id", "key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("result", {}).get("place_id")

def obtener_negocio_por_place_id(place_id: str):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "place_id,name,rating,user_ratings_total,formatted_address",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    result = data.get("result")
    if not result:
        return {"error": "Negocio no encontrado con ese link"}
    return {
        "nombre": result.get("name"),
        "direccion": result.get("formatted_address"),
        "rating": result.get("rating"),
        "total_resenas": result.get("user_ratings_total"),
        "place_id": result.get("place_id")
    }

def buscar_negocio(nombre: str, ubicacion: str = "El Salvador", maps_url: str = None):
    if maps_url:
        place_id = extraer_place_id_de_url(maps_url)
        if place_id:
            resultado = obtener_negocio_por_place_id(place_id)
            if "error" not in resultado:
                return resultado

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": f"{nombre} {ubicacion}",
        "inputtype": "textquery",
        "fields": "place_id,name,rating,user_ratings_total,formatted_address",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data["candidates"]:
        lugar = data["candidates"][0]
        return {
            "nombre": lugar.get("name"),
            "direccion": lugar.get("formatted_address"),
            "rating": lugar.get("rating"),
            "total_resenas": lugar.get("user_ratings_total"),
            "place_id": lugar.get("place_id")
        }
    return {"error": "Negocio no encontrado"}

def obtener_resenas(place_id: str):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "reviews,rating",
        "language": "es",
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    result = data.get("result", {})
    resenas = result.get("reviews", [])
    return {
        "rating_actual": result.get("rating"),
        "resenas": [
            {
                "autor": r.get("author_name"),
                "calificacion": r.get("rating"),
                "texto": r.get("text"),
                "fecha": r.get("relative_time_description")
            }
            for r in resenas
        ]
    }