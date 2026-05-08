import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def buscar_negocio(nombre: str, ubicacion: str = "El Salvador"):
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
            "total_reseñas": lugar.get("user_ratings_total"),
            "place_id": lugar.get("place_id")
        }
    return {"error": "Negocio no encontrado"}

def obtener_reseñas(place_id: str):
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
    reseñas = result.get("reviews", [])
    
    return {
        "rating_actual": result.get("rating"),
        "reseñas": [
            {
                "autor": r.get("author_name"),
                "calificacion": r.get("rating"),
                "texto": r.get("text"),
                "fecha": r.get("relative_time_description")
            }
            for r in reseñas
        ]
    }