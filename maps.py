import requests
import os
import re
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def extraer_query_de_url(maps_url: str):
    """Sigue el link y extrae place_id, cid, o texto de busqueda (q) segun lo que tenga la URL final."""
    try:
        response = requests.get(maps_url, allow_redirects=True, timeout=10)
        url_final = response.url

        match_place = re.search(r"place_id=([\w-]+)", url_final)
        if match_place:
            return ("place_id", match_place.group(1))

        match_cid = re.search(r"[?&]cid=(\d+)", url_final)
        if match_cid:
            return ("cid", match_cid.group(1))

        parsed = urllib.parse.urlparse(url_final)
        qs = urllib.parse.parse_qs(parsed.query)
        if "q" in qs:
            return ("query", qs["q"][0])

        return (None, None)
    except Exception:
        return (None, None)

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

def _buscar_por_texto(texto: str):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": texto,
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

def buscar_negocio(nombre: str, ubicacion: str = "El Salvador", maps_url: str = None):
    if maps_url:
        tipo, valor = extraer_query_de_url(maps_url)
        if tipo == "place_id":
            resultado = obtener_negocio_por_place_id(valor)
            if "error" not in resultado:
                return resultado
        elif tipo == "cid":
            place_id = buscar_place_id_por_cid(valor)
            if place_id:
                resultado = obtener_negocio_por_place_id(place_id)
                if "error" not in resultado:
                    return resultado
        elif tipo == "query":
            resultado = _buscar_por_texto(valor)
            if "error" not in resultado:
                return resultado

    return _buscar_por_texto(f"{nombre} {ubicacion}")

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