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