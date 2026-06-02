import whois
import ssl
import socket
import requests
import os
from datetime import datetime, timezone

def verificar_dominio(dominio: str):
    try:
        w = whois.whois(dominio)
        expiracion = w.expiration_date
        if isinstance(expiracion, list):
            expiracion = expiracion[0]
        if expiracion:
            ahora = datetime.now(timezone.utc) if expiracion.tzinfo else datetime.utcnow()
            dias_restantes = (expiracion - ahora).days
        else:
            dias_restantes = None
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
        s = ctx.wrap_socket(socket.socket(), server_hostname=dominio)
        s.settimeout(5)
        s.connect((dominio, 443))
        cert = s.getpeercert()
        s.close()
        expiracion = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        dias_restantes = (expiracion - datetime.utcnow()).days
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
        params = {"url": url, "key": api_key, "strategy": "mobile"}
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
        return {"error": str(e)}
    # fix 
