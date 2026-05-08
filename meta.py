import requests
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("META_APP_ID")
APP_SECRET = os.getenv("META_APP_SECRET")

def obtener_token_app():
    url = "https://graph.facebook.com/oauth/access_token"
    params = {
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "grant_type": "client_credentials"
    }
    res = requests.get(url, params=params)
    return res.json().get("access_token")

def obtener_datos_pagina(page_id: str, page_token: str):
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {
        "fields": "name,fan_count,followers_count,rating_count,overall_star_rating",
        "access_token": page_token
    }
    res = requests.get(url, params=params)
    return res.json()

def obtener_posts_pagina(page_id: str, page_token: str):
    url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
    params = {
        "fields": "message,created_time,likes.summary(true),comments.summary(true),shares",
        "limit": 10,
        "access_token": page_token
    }
    res = requests.get(url, params=params)
    data = res.json()
    
    posts = []
    for post in data.get("data", []):
        posts.append({
            "mensaje": post.get("message", "")[:100],
            "fecha": post.get("created_time"),
            "likes": post.get("likes", {}).get("summary", {}).get("total_count", 0),
            "comentarios": post.get("comments", {}).get("summary", {}).get("total_count", 0),
            "compartidos": post.get("shares", {}).get("count", 0)
        })
    return posts

def obtener_comentarios_recientes(page_id: str, page_token: str):
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    params = {
        "fields": "comments{message,from,created_time,like_count}",
        "limit": 5,
        "access_token": page_token
    }
    res = requests.get(url, params=params)
    data = res.json()
    
    comentarios = []
    for item in data.get("data", []):
        for comentario in item.get("comments", {}).get("data", []):
            comentarios.append({
                "autor": comentario.get("from", {}).get("name", "Anónimo"),
                "mensaje": comentario.get("message", ""),
                "fecha": comentario.get("created_time"),
                "likes": comentario.get("like_count", 0)
            })
    return comentarios[:10]