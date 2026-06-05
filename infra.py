import ssl
import socket
import requests
import os
from datetime import datetime

def verificar_dominio(dominio: str):
    try:
        res = requests.get(
            f"https://api.whoisfreaks.com/v1.0/whois?apiKey=free&whois=live&domainName={dominio}",
            timeout=10
        )
        data = res.json()
        expiracion = data.get("expiry_date", "No encontrada")
        return {
            "dominio": dominio,
            "registrador": data.get("registrar_name", "N/A"),
            "expiracion": expiracion,
            "dias_restantes": None,
            "alerta": False
        }
    except Exception as e:
        return {"error": "dominio_error: " + str(e)}

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
        return {"ssl_valido": False, "error": "ssl_error: " + str(e)}

def verificar_velocidad(url: str):
    try:
        api_key = os.getenv("PAGESPEED_API_KEY")
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
        return {"error": "velocidad_error: " + str(e)}