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
# HELPERS INTERNOS
# ==========================================

def _registrar_auditoria(id_usuario, accion):
    """
    Escribe un registro en la tabla Auditoria de SQL Server.
    Se llama desde login() y logout() para dejar historial permanente.
    No interrumpe el flujo si falla (la sesión Redis sigue siendo válida).

    Recibe:
        id_usuario (int): IdUsuario de la tabla Usuarios
        accion (str): 'login', 'logout' o 'expiro'
    """
    try:
        conn = pymssql.connect(**sql_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Auditoria (IdUsuario, Accion) VALUES (%d, %s)",
            (id_usuario, accion)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # No interrumpir el flujo si la auditoría falla


# ==========================================
# SESIONES
# ==========================================

def login(email, password):
    """
    Valida credenciales contra la tabla Usuarios de SQL Server y crea sesión en Redis.
    Además registra el evento en la tabla Auditoria (historial permanente en SQL).

    El TTL se determina automáticamente por rol:
      - admin / director → 600 segundos (dispositivo de confianza)
      - prensa           →   5 segundos (dispositivo no confiable)

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

    # 2. TTL según rol: prensa = no confiable, admin/director = confiable
    ttl = TTL_NO_CONFIABLE if usuario['Rol'] == 'prensa' else TTL_CONFIABLE
    clave = f"sesion:{email}"
    r.setex(clave, ttl, usuario['Rol'])

    # 3. Registrar el evento en SQL Auditoria (historial permanente)
    _registrar_auditoria(usuario['IdUsuario'], 'login')

    print(f"Login exitoso — {usuario['NombreCompleto']} ({usuario['Rol']}) — sesión: {ttl}s.")
    return ttl


def verificar_sesion(email, silencioso=False):
    """
    Verifica si la sesión del usuario sigue activa en Redis.
    Retorna el TTL restante en segundos, o None si expiró.

    Recibe:
        silencioso (bool): si True, no imprime nada (usado en el loop del menú)
    """
    clave = f"sesion:{email}"
    ttl_restante = r.ttl(clave)

    if ttl_restante <= 0:
        if not silencioso:
            print(f"Sesión de '{email}' expirada o inexistente.")
        return None

    if not silencioso:
        print(f"Sesión de '{email}' activa — {ttl_restante} segundos restantes.")
    return ttl_restante


def logout(email):
    """
    Cierra la sesión del usuario eliminando su clave de Redis.
    Además registra el evento en la tabla Auditoria de SQL Server.
    """
    clave = f"sesion:{email}"
    eliminado = r.delete(clave)

    if eliminado:
        # Registrar logout en SQL Auditoria (historial permanente)
        try:
            conn = pymssql.connect(**sql_config)
            cursor = conn.cursor(as_dict=True)
            cursor.execute(
                "SELECT IdUsuario FROM Usuarios WHERE Email = %s", (email,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                _registrar_auditoria(row['IdUsuario'], 'logout')
        except Exception:
            pass
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

if __name__ == "__main__":
    # Simula el flujo de la demo del profe:
    # 1. admin → TTL 600s (rol confiable)
    login('admin@f1.com', 'admin123')
    verificar_sesion('admin@f1.com')

    # 2. prensa → TTL 5s (rol no confiable)
    login('prensa@f1.com', 'prensa789')
    verificar_sesion('prensa@f1.com')

    # 3. Credenciales incorrectas
    login('prensa@f1.com', 'wrongpass')

    # 4. Ver todas las sesiones activas
    sesiones_activas()

    # 5. Logout manual
    logout('admin@f1.com')
    sesiones_activas()
