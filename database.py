import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv()

TOKENS_SUSCRIPCION_MENSUAL = int(os.getenv("TOKENS_SUSCRIPCION_MENSUAL", "30"))

def get_conn():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(db_url, sslmode="require")

def crear_tablas():
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                nombre TEXT,
                plan TEXT DEFAULT 'basico',
                tokens_disponibles INTEGER DEFAULT 100,
                tokens_usados INTEGER DEFAULT 0,
                fecha_registro TIMESTAMP DEFAULT NOW(),
                fecha_renovacion TIMESTAMP DEFAULT NOW() + INTERVAL '1 month',
                activo BOOLEAN DEFAULT TRUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS uso_tokens (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER REFERENCES clientes(id),
                tipo TEXT NOT NULL,
                descripcion TEXT,
                tokens_consumidos INTEGER DEFAULT 1,
                fecha TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Tablas creadas correctamente")
    except Exception as e:
        print(f"Error creando tablas: {e}")

crear_tablas()

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

def registrar_cliente(email: str, nombre: str = "", plan: str = "basico"):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clientes (email, nombre, plan, tokens_disponibles)
            VALUES (%s, %s, %s, 100)
            ON CONFLICT (email) DO NOTHING
            RETURNING id, tokens_disponibles
        """, (email, nombre, plan))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if result:
            return {"ok": True, "cliente_id": result[0], "tokens": result[1]}
        return {"ok": False, "error": "Email ya registrado"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verificar_tokens(email: str):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, tokens_disponibles, tokens_usados, plan FROM clientes WHERE email = %s AND activo = TRUE", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return {"ok": False, "error": "Cliente no encontrado"}
        return {"ok": True, "cliente_id": row[0], "tokens_disponibles": row[1], "tokens_usados": row[2], "plan": row[3]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def consumir_token(email: str, tipo: str, descripcion: str = ""):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, tokens_disponibles FROM clientes WHERE email = %s AND activo = TRUE", (email,))
        row = cur.fetchone()
        if not row or row[1] < 1:
            conn.close()
            return {"ok": False, "error": "Sin tokens disponibles"}
        cliente_id = row[0]
        cur.execute("UPDATE clientes SET tokens_disponibles = tokens_disponibles - 1, tokens_usados = tokens_usados + 1 WHERE id = %s", (cliente_id,))
        cur.execute("INSERT INTO uso_tokens (cliente_id, tipo, descripcion) VALUES (%s, %s, %s)", (cliente_id, tipo, descripcion))
        conn.commit()
        cur.close()
        conn.close()
        return {"ok": True, "tokens_restantes": row[1] - 1}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def actualizar_suscripcion(email: str, event: str, nombre: str = ""):
    try:
        conn = get_conn()
        cur = conn.cursor()
        if event == "activated":
            cur.execute("""
                INSERT INTO clientes (email, nombre, plan, tokens_disponibles, activo)
                VALUES (%s, %s, 'suscripcion', %s, TRUE)
                ON CONFLICT (email) DO UPDATE
                SET tokens_disponibles = EXCLUDED.tokens_disponibles, activo = TRUE, plan = 'suscripcion'
                RETURNING id, tokens_disponibles, activo
            """, (email, nombre, TOKENS_SUSCRIPCION_MENSUAL))
        elif event in ("cancelled", "payment_failed"):
            cur.execute("""
                UPDATE clientes SET activo = FALSE WHERE email = %s
                RETURNING id, tokens_disponibles, activo
            """, (email,))
        else:
            cur.close()
            conn.close()
            return {"ok": False, "error": "Evento no soportado"}
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if not result:
            return {"ok": False, "error": "Cliente no encontrado"}
        return {"ok": True, "cliente_id": result[0], "tokens_disponibles": result[1], "activo": result[2]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def recargar_tokens(email: str, cantidad: int = 100):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE clientes SET tokens_disponibles = tokens_disponibles + %s WHERE email = %s", (cantidad, email))
        conn.commit()
        cur.close()
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}