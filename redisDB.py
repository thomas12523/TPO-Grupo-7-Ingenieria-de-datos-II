import redis
import pymssql

# Conexión a Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Config de SQL Server (para validar que el usuario existe antes de crear sesión)
sql_config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master'
}

TTL_CONFIABLE     = 600  # 10 minutos
TTL_NO_CONFIABLE  = 5    # 5 segundos


# ==========================================
# SESIONES
# ==========================================

def login(email, password, dispositivo_confiable: bool):
    """
    Valida credenciales contra la tabla Usuarios de SQL Server y crea sesión en Redis.
    Si el dispositivo es de confianza la sesión dura 10 minutos, si no 5 segundos.
    Retorna el TTL asignado, o None si las credenciales son incorrectas.
    """
    # 1. Validar credenciales en SQL Server (fuente de verdad)
    conn = pymssql.connect(**sql_config)
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT IdUsuario, NombreCompleto, Rol FROM Usuarios WHERE Email = %s AND Password = %s",
        (email, password)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        print(f"Credenciales incorrectas para '{email}'.")
        return None

    # 2. Crear sesión en Redis con TTL
    ttl = TTL_CONFIABLE if dispositivo_confiable else TTL_NO_CONFIABLE
    clave = f"sesion:{email}"
    r.setex(clave, ttl, usuario['Rol'])

    print(f"Login exitoso — {usuario['NombreCompleto']} ({usuario['Rol']}) — sesión: {ttl}s.")
    return ttl


def verificar_sesion(email):
    """
    Verifica si la sesión del usuario sigue activa en Redis.
    Retorna el TTL restante en segundos, o None si expiró.
    """
    clave = f"sesion:{email}"
    ttl_restante = r.ttl(clave)

    if ttl_restante <= 0:
        print(f"Sesión de '{email}' expirada o inexistente.")
        return None

    print(f"Sesión de '{email}' activa — {ttl_restante} segundos restantes.")
    return ttl_restante


def logout(email):
    """Cierra la sesión del usuario eliminando su clave de Redis."""
    clave = f"sesion:{email}"
    eliminado = r.delete(clave)

    if eliminado:
        print(f"Sesión de '{email}' cerrada.")
    else:
        print(f"No había sesión activa para '{email}'.")


def sesiones_activas():
    """
    Devuelve todas las sesiones activas con su TTL restante.
    Útil para mostrar en el GUI cuántos usuarios están conectados.
    """
    claves = r.keys("sesion:*")
    sesiones = []

    print("\n--- Sesiones activas ---")
    if not claves:
        print("  No hay sesiones activas.")
        return []

    for clave in claves:
        email = clave.replace("sesion:", "")
        ttl = r.ttl(clave)
        sesiones.append({'email': email, 'ttl_restante': ttl})
        print(f"  {email} — {ttl} segundos restantes")

    return sesiones


# ==========================================
# CRUD ADICIONAL
# ==========================================

def guardar_dato_temporal(clave, valor, ttl_segundos):
    """Guarda cualquier dato temporal en Redis con TTL. Uso general."""
    r.setex(clave, ttl_segundos, valor)
    print(f"Dato '{clave}' guardado por {ttl_segundos} segundos.")


def obtener_dato(clave):
    """Lee un valor de Redis. Retorna None si no existe o expiró."""
    valor = r.get(clave)
    if valor is None:
        print(f"Clave '{clave}' no encontrada o expirada.")
    return valor


def eliminar_dato(clave):
    """Elimina una clave de Redis manualmente."""
    r.delete(clave)
    print(f"Clave '{clave}' eliminada.")


# ==========================================
# EJECUCIÓN
# ==========================================

# Simula el flujo de la demo del profe:
# 1. Login con dispositivo de confianza
login('admin@f1.com', 'admin123', dispositivo_confiable=True)
verificar_sesion('admin@f1.com')

# 2. Login sin dispositivo de confianza (sesión de 5 segundos)
login('prensa@f1.com', 'prensa789', dispositivo_confiable=False)
verificar_sesion('prensa@f1.com')

# 3. Credenciales incorrectas
login('prensa@f1.com', 'wrongpass', dispositivo_confiable=True)

# 4. Ver todas las sesiones activas
sesiones_activas()

# 5. Logout manual
logout('admin@f1.com')
sesiones_activas()
