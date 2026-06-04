import ssl
import socket
import requests
import os
import subprocess
from datetime import datetime

def verificar_dominio(dominio: str):
    try:
        result = subprocess.run(
            ['whois', dominio], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        output = result.stdout
        expiracion_str = "No encontrada"
        for line in output.split('\n'):
            line_lower = line.lower()
            if 'expir' in line_lower and ':' in line:
                expiracion_str = line.strip()
                break
        return {
            "dominio": dominio,
            "expiracion": expiracion_str,
            "dias_restantes": None,
            "alerta": False,
            "raw": output[:300]
        }
    except Exception as e:
        return {"error": "dominio_error: " + str(e)}

def verificar_dominio(dominio: str):
    try:
        res = requests.get(f"https://api.whoisfreaks.com/v1.0/whois?apiKey=free&whois=live&domainName={dominio}", timeout=10)
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
        return {"error": "velocidad_error: " + str(e)}