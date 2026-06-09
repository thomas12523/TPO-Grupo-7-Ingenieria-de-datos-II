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

TTL_SESION = 600  # 10 minutos de inactividad — director y prensa


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

    TTL según rol:
      - admin    → sin TTL (sesión permanente hasta logout explícito)
      - director → 600 segundos de inactividad (TTL deslizante)
      - prensa   → 600 segundos de inactividad (TTL deslizante)

    Retorna (ttl, nombre) si las credenciales son correctas, None si no.
      ttl = None para admin (sin expiración), int para el resto.
    """
    conn = pymssql.connect(**sql_config)
    cursor = conn.cursor(as_dict=True)
    cursor.execute(
        "SELECT IdUsuario, NombreCompleto, Rol FROM Usuarios WHERE Email = %s AND Password = %s",
        (email, password)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        print(f"  Credenciales incorrectas.")
        return None

    clave = f"sesion:{email}"

    if usuario['Rol'] == 'admin':
        r.set(clave, usuario['Rol'])  # sin TTL — sesión permanente
        ttl_display = "sin límite"
        ttl = None
    else:
        r.setex(clave, TTL_SESION, usuario['Rol'])  # TTL deslizante
        ttl_display = f"{TTL_SESION}s de inactividad"
        ttl = TTL_SESION

    _registrar_auditoria(usuario['IdUsuario'], 'login')

    print(f"  Bienvenido, {usuario['NombreCompleto']} ({usuario['Rol']}) — sesión: {ttl_display}.")
    return ttl, usuario['NombreCompleto']


def renovar_sesion(email):
    """
    Resetea el TTL de la sesión activa (TTL deslizante).
    Solo aplica a roles con TTL — admin no tiene expiración y se omite.
    Se llama después de cada acción exitosa del usuario en el menú.
    """
    clave = f"sesion:{email}"
    rol = r.get(clave)
    if rol is None or rol == 'admin':
        return
    r.expire(clave, TTL_SESION)


def verificar_sesion(email, silencioso=False):
    """
    Verifica si la sesión del usuario sigue activa en Redis.

    Valores de TTL en Redis:
      -2 → clave no existe (sesión expirada o nunca creada)
      -1 → clave existe sin TTL (admin)
      >0 → segundos restantes

    Retorna el TTL restante (o -1 para admin), None si la sesión no existe.
    """
    clave = f"sesion:{email}"
    ttl_restante = r.ttl(clave)

    if ttl_restante == -2:  # clave no existe → sesión expirada
        if not silencioso:
            print(f"  Sesión de '{email}' expirada o inexistente.")
        return None

    if not silencioso:
        if ttl_restante == -1:
            print(f"  Sesión de '{email}' activa — sin límite de tiempo.")
        else:
            print(f"  Sesión de '{email}' activa — {ttl_restante}s restantes.")

    return ttl_restante


def logout(email):
    """
    Cierra la sesión del usuario eliminando su clave de Redis.
    Además registra el evento en la tabla Auditoria de SQL Server.
    """
    clave = f"sesion:{email}"
    eliminado = r.delete(clave)

    if eliminado:
        try:
            conn = pymssql.connect(**sql_config)
            cursor = conn.cursor(as_dict=True)
            cursor.execute("SELECT IdUsuario FROM Usuarios WHERE Email = %s", (email,))
            row = cursor.fetchone()
            conn.close()
            if row:
                _registrar_auditoria(row['IdUsuario'], 'logout')
        except Exception:
            pass
        print(f"  Sesión de '{email}' cerrada.")
    else:
        print(f"  No había sesión activa para '{email}'.")


def sesiones_activas():
    """
    Muestra todas las sesiones activas con su TTL restante.
    """
    claves = r.keys("sesion:*")

    print("\n--- Sesiones activas ---")
    if not claves:
        print("  No hay sesiones activas.")
        return []

    sesiones = []
    for clave in claves:
        email = clave.replace("sesion:", "")
        ttl = r.ttl(clave)
        ttl_display = "sin límite" if ttl == -1 else f"{ttl}s restantes"
        sesiones.append({'email': email, 'ttl_restante': ttl})
        print(f"  {email} — {ttl_display}")

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
    login('admin@f1.com', 'admin123')
    verificar_sesion('admin@f1.com')        # → sin límite

    login('prensa@f1.com', 'prensa789')
    verificar_sesion('prensa@f1.com')       # → 600s restantes

    login('prensa@f1.com', 'wrongpass')     # → credenciales incorrectas

    sesiones_activas()
    logout('admin@f1.com')
    sesiones_activas()
