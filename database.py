import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(db_url, sslmode="require")

def crear_tabla():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analisis (
                id SERIAL PRIMARY KEY,
                negocio TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT NOW(),
                rating NUMERIC,
                total_resenas INTEGER,
                direccion TEXT,
                sentimiento TEXT,
                porcentaje_positivo INTEGER,
                porcentaje_negativo INTEGER,
                alerta_critica BOOLEAN,
                resumen TEXT,
                recomendacion TEXT,
                problemas JSONB,
                fortalezas JSONB
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creando tabla: {e}")

crear_tabla()

def guardar_analisis(negocio: str, datos_negocio: dict, datos_analisis: dict):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO analisis (negocio, rating, total_resenas, direccion, sentimiento, porcentaje_positivo, porcentaje_negativo, alerta_critica, resumen, recomendacion, problemas, fortalezas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            negocio,
            datos_negocio.get("rating"),
            datos_negocio.get("total_resenas"),
            datos_negocio.get("direccion"),
            datos_analisis.get("sentimiento_general"),
            datos_analisis.get("porcentaje_positivo"),
            datos_analisis.get("porcentaje_negativo"),
            datos_analisis.get("alerta_critica"),
            datos_analisis.get("resumen"),
            datos_analisis.get("recomendacion"),
            json.dumps(datos_analisis.get("principales_problemas")),
            json.dumps(datos_analisis.get("principales_fortalezas"))
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"guardado": True}
    except Exception as e:
        return {"guardado": False, "error": str(e)}

def obtener_historial(negocio: str):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, negocio, fecha, rating, total_resenas, sentimiento, porcentaje_positivo, porcentaje_negativo, alerta_critica, resumen, recomendacion, problemas, fortalezas, direccion
            FROM analisis WHERE negocio ILIKE %s ORDER BY fecha DESC
        """, (f"%{negocio}%",))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id": r[0], "negocio": r[1], "fecha": str(r[2]),
                "rating": float(r[3]) if r[3] else None,
                "total_resenas": r[4], "sentimiento": r[5],
                "porcentaje_positivo": r[6], "porcentaje_negativo": r[7],
                "alerta_critica": r[8], "resumen": r[9],
                "recomendacion": r[10], "problemas": r[11],
                "fortalezas": r[12], "direccion": r[13]
            }
            for r in rows
        ]
    except Exception as e:
        return []