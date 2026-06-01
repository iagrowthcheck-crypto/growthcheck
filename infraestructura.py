from infraestructura import verificar_dominio, verificar_ssl, verificar_velocidad
import whois
import ssl
import socket
import requests
import os
from datetime import datetime

def verificar_dominio(dominio: str):
    try:
        w = whois.whois(dominio)
        expiracion = w.expiration_date
        if isinstance(expiracion, list):
            expiracion = expiracion[0]
        dias_restantes = (expiracion - datetime.now()).days if expiracion else None
        return {
            "dominio": dominio,
            "registrador": w.registrar,
            "expiracion": str(expiracion),
            "dias_restantes": dias_restantes,
            "alerta": dias_restantes < 30 if dias_restantes else False
        }
    except Exception as e:
        return {"error": str(e)}

def verificar_ssl(dominio: str):
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=dominio) as s:
            s.settimeout(5)
            s.connect((dominio, 443))
            cert = s.getpeercert()
        expiracion = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        dias_restantes = (expiracion - datetime.now()).days
        return {
            "ssl_valido": True,
            "expiracion": str(expiracion),
            "dias_restantes": dias_restantes,
            "alerta": dias_restantes < 30
        }
    except Exception as e:
        return {"ssl_valido": False, "error": str(e)}

def verificar_velocidad(url: str):
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": url,
            "key": api_key,
            "strategy": "mobile"
        }
        res = requests.get(endpoint, params=params)
        data = res.json()
        cats = data.get("lighthouseResult", {}).get("categories", {})
        perf = cats.get("performance", {}).get("score", 0)
        audits = data.get("lighthouseResult", {}).get("audits", {})
        fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
        lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
        return {
            "performance_score": round(perf * 100),
            "first_contentful_paint": fcp,
            "largest_contentful_paint": lcp,
            "alerta": perf < 0.5
        }
    except Exception as e:
        return {"error": str(e)@app.get("/dominio/{dominio}")
def get_dominio(dominio: str):
    return verificar_dominio(dominio)

@app.get("/ssl/{dominio}")
def get_ssl(dominio: str):
    return verificar_ssl(dominio)

@app.get("/velocidad")
def get_velocidad(url: str):
    return verificar_velocidad(url)}