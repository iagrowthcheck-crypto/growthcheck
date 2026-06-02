import pythonwhois as whois
import ssl
import socket
import requests
import os
from datetime import datetime, timezone

def verificar_dominio(dominio: str):
    try:
        import subprocess
        result = subprocess.run(['whois', dominio], capture_output=True, text=True, timeout=10)
        output = result.stdout
        expiracion_str = "No encontrada"
        dias_restantes = None
        for line in output.split('\n'):
            if 'expir' in line.lower() or 'Expir' in line:
                expiracion_str = line.strip()
                break
        return {
            "dominio": dominio,
            "expiracion": expiracion_str,
            "dias_restantes": dias_restantes,
            "alerta": False,
            "info_completa": output[:500]
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