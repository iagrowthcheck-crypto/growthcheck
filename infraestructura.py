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
        dias_restantes = None
        if expiracion:
            try:
                import calendar
                exp_ts = calendar.timegm(expiracion.timetuple())
                now_ts = calendar.timegm(datetime.utcnow().timetuple())
                dias_restantes = (exp_ts - now_ts) // 86400
            except Exception:
                dias_restantes = None
        return {
            "dominio": dominio,
            "registrador": str(w.registrar),
            "expiracion": str(expiracion),
            "dias_restantes": dias_restantes,
            "alerta": dias_restantes is not None and dias_restantes < 30
        }
    except Exception as e:
        return {"error": str(e)}

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