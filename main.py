import sys
import time
from datetime import datetime

# Importamos los módulos de bases de datos con alias para que main los use por nombre corto
import sql         as db_sql
import redisDB     as db_redis
import cassandraDB as db_cassandra
import mongoDB     as db_mongo
import neo4jDB     as db_neo4j


def _mensaje_error_sql(e):
    """Traduce errores pymssql comunes a mensajes legibles."""
    msg = str(e)
    if '547' in msg:
        return "ID inexistente — verificá que el ID ingresado exista en la lista."
    if '2627' in msg or '2601' in msg:
        return "Ya existe un registro con esos datos."
    if '241' in msg or 'conversion' in msg.lower():
        return "Formato de fecha inválido."
    return msg.split('\\n')[0]  # primera línea del error original


def _pedir_int(prompt):
    """Pide un entero hasta que el usuario ingrese uno válido."""
    while True:
        valor = input(prompt).strip()
        if valor.isdigit():
            return int(valor)
        print("  Ingresá un número válido.")


def _pedir_fecha(prompt):
    """Pide una fecha en formato YYYY-MM-DD hasta que sea válida."""
    while True:
        valor = input(prompt).strip()
        try:
            datetime.strptime(valor, "%Y-%m-%d")
            return valor
        except ValueError:
            print("  Formato inválido. Usá YYYY-MM-DD (ej: 1994-09-01).")

def _pedir_float(prompt):
    """Pide un decimal hasta que el usuario ingrese uno válido."""
    while True:
        valor = input(prompt).strip()
        try:
            return float(valor)
        except ValueError:
            print("  Ingresá un número válido (ej: 2.500).")

_PUNTOS_F1 = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

def mostrar_encabezado():
    print("="*60)
    print("       SISTEMA DE GESTIÓN - FÓRMULA 1 (GRUPO 7)       ")
    print("="*60)

def verificar_conexiones():
    """Realiza un ping a todas las bases de datos para asegurar conectividad inicial."""
    print("\n[⏳] Verificando conexiones a las bases de datos...")
    time.sleep(0.5)

    # 1. SQL Server
    try:
        conn = db_sql.obtener_conexion()
        conn.close()
        print("  ✅ SQL Server  : Conectado")
    except Exception as e:
        print(f"  ❌ SQL Server  : Error -> {e}")

    # 2. Redis
    try:
        db_redis.r.ping()
        print("  ✅ Redis       : Conectado")
    except Exception as e:
        print(f"  ❌ Redis       : Error -> {e}")

    # 3. Cassandra
    try:
        db_cassandra.conectar()
        db_cassandra.session.execute("SELECT release_version FROM system.local")
        print("  ✅ Cassandra   : Conectado")
    except Exception as e:
        print(f"  ❌ Cassandra   : Error -> {e}")

    # 4. MongoDB
    try:
        db_mongo.mongo_client.admin.command('ping')
        print("  ✅ MongoDB     : Conectado")
    except Exception as e:
        print(f"  ❌ MongoDB     : Error -> {e}")

    # 5. Neo4j
    try:
        db_neo4j.driver.verify_connectivity()
        print("  ✅ Neo4j       : Conectado")
    except Exception as e:
        print(f"  ❌ Neo4j       : Error -> {e}")
        
    print("-" * 60)

def login_sistema():
    """Maneja la autenticación usando SQL (validación) y Redis (sesión)."""
    intentos = 3
    while intentos > 0:
        email    = input("\nEmail: ").strip()
        password = input("Contraseña: ").strip()

        resultado = db_redis.login(email, password)

        if resultado:
            ttl, nombre = resultado
            return email, nombre
        else:
            intentos -= 1
            if intentos > 0:
                print(f"  Credenciales inválidas. Intentos restantes: {intentos}")

    print("\nAcceso bloqueado. Cerrando sistema.")
    sys.exit()

def _sincronizar_en_segundo_plano():
    """
    Transfiere los datos de SQL Server (fuente de verdad) a cada base NoSQL.

    Diseño de consistencia eventual:
      - SQL es ACID y es siempre la fuente correcta.
      - Cada NoSQL se sincroniza de forma independiente: si una falla, las demás
        continúan. No hay rollback distribuido porque la operación es idempotente
        (borrar + reinsertar), por lo que re-ejecutar la sync restaura la consistencia.
      - Si una base NoSQL queda desactualizada, el dato real sigue en SQL.

    Retorna dict con el estado de cada base: True si OK, mensaje de error si falló.
    """
    estado = {}

    # Cassandra — CU1 y CU2
    print("  ⏳ Cassandra...", end="", flush=True)
    try:
        db_cassandra.crear_keyspace_y_tablas()
        db_cassandra.insertar_datos()
        estado['cassandra'] = True
        print("\r  ✅ Cassandra   ")
    except Exception as e:
        estado['cassandra'] = str(e)
        print(f"\r  ❌ Cassandra    → {e}")

    # MongoDB — CU3 y CU4
    print("  ⏳ MongoDB...", end="", flush=True)
    try:
        db_mongo.crear_colecciones_e_indices()
        db_mongo.insertar_datos()
        estado['mongodb'] = True
        print("\r  ✅ MongoDB     ")
    except Exception as e:
        estado['mongodb'] = str(e)
        print(f"\r  ❌ MongoDB      → {e}")

    # Neo4j — CU5 y CU6
    print("  ⏳ Neo4j...", end="", flush=True)
    try:
        db_neo4j.poblar_desde_sql()
        estado['neo4j'] = True
        print("\r  ✅ Neo4j       ")
    except Exception as e:
        estado['neo4j'] = str(e)
        print(f"\r  ❌ Neo4j        → {e}")

    fallidas = [db for db, ok in estado.items() if ok is not True]
    if fallidas:
        print(f"\n  [⚠️] Datos desactualizados en: {', '.join(fallidas)}")
        print(f"       El dato real sigue en SQL Server. Se corrige en el próximo CRUD.")
    return estado

def menu_crud():
    """
    Submenú CRUD sobre SQL Server (fuente de verdad).

    Las operaciones modifican tablas que alimentan directamente los casos de uso:
      - Resultados → CU2 (victorias por equipo), CU3 (vueltas rápidas), CU5 (podios)
      - PitStops   → CU4 (promedio de pit stops)

    Toda escritura ocurre primero en SQL (ACID). El sync posterior actualiza
    Cassandra, MongoDB y Neo4j de forma independiente (consistencia eventual).
    """
    while True:
        sep = "─" * 50
        print(f"\n{sep}")
        print(f"       GESTIÓN DE DATOS (CRUD)  [SQL Server]")
        print(sep)
        print("  L. Listar Pilotos, Equipos y Carreras")
        print(f"  {'─'*46}")
        print("  1. Registrar Resultado de Carrera      → CU2 / CU3 / CU5")
        print("  2. Eliminar Resultado de Carrera       → CU2 / CU3 / CU5")
        print("  3. Registrar Pit Stop                  → CU4")
        print("  4. Eliminar Pit Stops (Piloto+Carrera) → CU4")
        print(f"  {'─'*46}")
        print("  0. Volver al menú principal")

        opcion = input("\nSeleccione una operación: ").strip().upper()
        hubo_cambios = False

        if opcion == 'L':
            db_sql.listar_pilotos()
            db_sql.listar_equipos()
            db_sql.listar_carreras()

        elif opcion == '1':
            db_sql.listar_pilotos()
            db_sql.listar_carreras()
            id_piloto  = _pedir_int("  ID del Piloto: ")
            id_carrera = _pedir_int("  ID de la Carrera: ")
            posicion   = _pedir_int("  Posición final (1=victoria, ≤3=podio): ")
            puntos     = _PUNTOS_F1.get(posicion, 0)
            print(f"  Puntos automáticos: {puntos}")
            try:
                db_sql.insertar_resultado(id_piloto, id_carrera, posicion, puntos)
                hubo_cambios = True
            except Exception as e:
                print(f"  [❌] {_mensaje_error_sql(e)}")

        elif opcion == '2':
            db_sql.listar_resultados()
            id_piloto  = _pedir_int("  ID del Piloto: ")
            id_carrera = _pedir_int("  ID de la Carrera: ")
            try:
                hubo_cambios = db_sql.eliminar_resultado(id_piloto, id_carrera)
            except Exception as e:
                print(f"  [❌] {_mensaje_error_sql(e)}")

        elif opcion == '3':
            db_sql.listar_pilotos()
            db_sql.listar_carreras()
            id_piloto     = _pedir_int("  ID del Piloto: ")
            id_carrera    = _pedir_int("  ID de la Carrera: ")
            numero_parada = _pedir_int("  Número de parada (1, 2, 3...): ")
            tiempo_parada = _pedir_float("  Tiempo de parada en segundos (ej: 2.500): ")
            try:
                db_sql.insertar_pit_stop_sql(id_piloto, id_carrera, numero_parada, tiempo_parada)
                hubo_cambios = True
            except Exception as e:
                print(f"  [❌] {_mensaje_error_sql(e)}")

        elif opcion == '4':
            db_sql.listar_pit_stops()
            id_piloto  = _pedir_int("  ID del Piloto: ")
            id_carrera = _pedir_int("  ID de la Carrera: ")
            try:
                hubo_cambios = db_sql.eliminar_pit_stops_piloto(id_piloto, id_carrera)
            except Exception as e:
                print(f"  [❌] {_mensaje_error_sql(e)}")

        elif opcion == '0':
            break
        else:
            print("Opción no válida.")

        if hubo_cambios:
            print("\n[🔄] Propagando cambios a entornos de lectura (Cassandra, MongoDB, Neo4j)...")
            estado = _sincronizar_en_segundo_plano()
            ok_count = sum(1 for v in estado.values() if v is True)
            print(f"[✅] SQL actualizado. Entornos NoSQL sincronizados: {ok_count}/{len(estado)}.")

def menu_principal(email):
    while True:
        # Verificar sesión activa antes de cada acción (silencioso = no spamea)
        if not db_redis.verificar_sesion(email, silencioso=True):
            print("\n⚠️  Sesión expirada. Cerrando sesión automáticamente.")
            break

        print("\n" + "="*50)
        print("               MENÚ PRINCIPAL               ")
        print("="*50)
        print("1. CU1: Pilotos con múltiples campeonatos mundiales")
        print("2. CU2: Equipos con más victorias históricas")
        print("3. CU3: Pilotos con la vuelta más rápida en carreras")
        print("4. CU4: Promedio de pit stops por carrera")
        print("5. CU5: Pilotos eficientes (>10 podios y >5 temporadas)")
        print("6. CU6: Ranking de países con más carreras o circuitos")
        print("-" * 50)
        print("7. Gestión de Datos Maestros (CRUD)")
        print("8. Ver sesiones activas en el sistema")
        print("0. Salir y cerrar sesión")
        
        opcion = input("\nSeleccione una opción: ")
        
        try:
            if opcion == '1':
                db_cassandra.cu1_pilotos_multicampeon()
            elif opcion == '2':
                db_cassandra.cu2_equipos_mas_victorias()
            elif opcion == '3':
                db_mongo.cu3_pilotos_vuelta_rapida()
            elif opcion == '4':
                db_mongo.cu4_promedio_pit_stops_por_carrera()
            elif opcion == '5':
                db_neo4j.pilotosEficientes()
            elif opcion == '6':
                db_neo4j.paisConMasCarreras()
                db_neo4j.paisConMas1Circuito()
            elif opcion == '7':
                menu_crud()
            elif opcion == '8':
                db_redis.sesiones_activas()
            elif opcion == '0':
                break
            else:
                print("Opción no válida. Intente nuevamente.")

            # TTL deslizante: cada acción exitosa renueva la sesión
            if opcion not in ('0',):
                db_redis.renovar_sesion(email)

        except Exception as e:
            print(f"\n  [❌] Error al ejecutar la consulta: {e}")
            print(f"       Verificá que la base de datos correspondiente esté activa.")
        
        if opcion not in ('7', '3'):
            input("\nPresione ENTER para continuar...")

def main():
    mostrar_encabezado()
    
    # 1. Verificar estado de la infraestructura
    verificar_conexiones()
    
    # 2. Asegurar esquema SQL inicial + datos base (rellenar se llama dentro de crear)
    print("\n[🗄️ ] Verificando esquema SQL...")
    db_sql.crear_tablas_f1()

    # 3. Autenticación
    email_actual, nombre_actual = login_sistema()
    
    # 4. Sincronización inicial: SQL → NoSQL
    print("\n[🔄] Sincronizando bases de datos...")
    estado = _sincronizar_en_segundo_plano()
    ok_count = sum(1 for v in estado.values() if v is True)
    print(f"[{'✅' if ok_count == len(estado) else '⚠️'}] Sistema listo: {ok_count}/{len(estado)} bases sincronizadas.")

    # 5. Flujo de trabajo principal
    menu_principal(email_actual)

    # 6. Cierre seguro
    db_redis.logout(email_actual)
    print("\n  Sesión finalizada. ¡Hasta luego!")

if __name__ == "__main__":
    main()