import sys
import time

# Importamos los módulos de bases de datos con alias para que main los use por nombre corto
import sql         as db_sql
import redisDB     as db_redis
import cassandraDB as db_cassandra
import mongoDB     as db_mongo
import neo4jDB     as db_neo4j

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
        print(" SQL Server: Conectado")
    except Exception as e:
        print(f"   SQL Server: Error de conexión -> {e}")

    # 2. Redis
    try:
        db_redis.r.ping()
        print("   Redis: Conectado")
    except Exception as e:
        print(f"   Redis: Error de conexión -> {e}")

    # 3. Cassandra
    try:
        db_cassandra.conectar()
        db_cassandra.session.execute("SELECT release_version FROM system.local")
        print("   Cassandra: Conectado")
    except Exception as e:
        print(f"   Cassandra: Error de conexión -> {e}")

    # 4. MongoDB
    try:
        db_mongo.mongo_client.admin.command('ping')
        print("   MongoDB: Conectado")
    except Exception as e:
        print(f"   MongoDB: Error de conexión -> {e}")

    # 5. Neo4j
    try:
        db_neo4j.driver.verify_connectivity()
        print("   Neo4j: Conectado")
    except Exception as e:
        print(f"   Neo4j: Error de conexión -> {e}")
        
    print("-" * 60)

def login_sistema():
    """Maneja la autenticación usando SQL (validación) y Redis (sesión)."""
    intentos = 3
    while intentos > 0:
        email    = input("\nEmail: ").strip()
        password = input("Contraseña: ").strip()

        # TTL se determina automáticamente por rol (prensa=5s, admin/director=600s)
        ttl = db_redis.login(email, password)

        if ttl:
            return email
        else:
            intentos -= 1
            print(f"Credenciales inválidas. Intentos restantes: {intentos}")

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

    # Cassandra — resultados históricos para CU1 y CU2
    try:
        db_cassandra.crear_keyspace_y_tablas()
        db_cassandra.insertar_datos()
        estado['cassandra'] = True
    except Exception as e:
        estado['cassandra'] = str(e)
        print(f"  [⚠️] Cassandra no actualizada: {e}")

    # MongoDB — pit stops y penalizaciones para CU3 y CU4
    try:
        db_mongo.crear_colecciones_e_indices()
        db_mongo.insertar_datos()
        estado['mongodb'] = True
    except Exception as e:
        estado['mongodb'] = str(e)
        print(f"  [⚠️] MongoDB no actualizada: {e}")

    # Neo4j — grafo piloto↔temporada y carrera↔circuito para CU5 y CU6
    try:
        db_neo4j.poblar_desde_sql()
        estado['neo4j'] = True
    except Exception as e:
        estado['neo4j'] = str(e)
        print(f"  [⚠️] Neo4j no actualizado: {e}")

    fallidas = [db for db, ok in estado.items() if ok is not True]
    if fallidas:
        print(f"  [⚠️] Entornos de lectura con datos desactualizados: {', '.join(fallidas)}")
        print(f"       Los datos reales siguen en SQL Server. Re-ejecutar sync los corrige.")
    return estado

def menu_crud():
    """
    Submenú CRUD sobre SQL Server (fuente de verdad).

    Toda escritura ocurre primero en SQL (ACID). Si la operación SQL es exitosa,
    se dispara la sincronización hacia los NoSQL. Si un NoSQL falla durante el sync,
    SQL ya tiene el dato correcto y el sync es idempotente: re-ejecutarlo en cualquier
    momento restaura la consistencia sin pérdida de datos (consistencia eventual).

    Los NoSQL no se modifican directamente desde este menú: son entornos de lectura
    optimizados, no fuentes de escritura.
    """
    while True:
        print("\n" + "-"*40)
        print("      GESTIÓN DE DATOS (CRUD)      ")
        print("-"*41)
        print("  Fuente de verdad: SQL Server")
        print("  Los cambios se propagan automáticamente a Cassandra, MongoDB y Neo4j.")
        print("-"*41)
        print("--- Ver datos ---")
        print("L. Listar Pilotos y Equipos")
        print("--- Modificar ---")
        print("1. Insertar nuevo Piloto")
        print("2. Actualizar Director de Equipo")
        print("3. Cambiar Piloto de Equipo (Transferencia)")
        print("4. Eliminar Piloto")
        print("0. Volver al menú principal")

        opcion = input("\nSeleccione una operación: ").strip().upper()

        hubo_cambios = False

        if opcion == 'L':
            # READ: mostrar estado actual de SQL antes de operar
            db_sql.listar_pilotos()
            db_sql.listar_equipos()

        elif opcion == '1':
            db_sql.listar_equipos()          # mostrar IDs disponibles antes de pedir input
            nombre    = input("Nombre del piloto: ")
            fecha     = input("Fecha de nacimiento (YYYY-MM-DD): ")
            nac       = input("Nacionalidad: ")
            id_equipo = int(input("ID del Equipo: "))
            try:
                db_sql.insertar_piloto_manual(nombre, fecha, nac, id_equipo)
                hubo_cambios = True
            except Exception as e:
                print(f"  [❌] Error al insertar en SQL: {e}. No se propagó a los NoSQL.")

        elif opcion == '2':
            db_sql.listar_equipos()          # mostrar IDs disponibles
            id_equipo  = int(input("ID del Equipo a modificar: "))
            nuevo_dir  = input("Nombre del nuevo Director: ")
            try:
                db_sql.actualizar_director_equipo(id_equipo, nuevo_dir)
                hubo_cambios = True
            except Exception as e:
                print(f"  [❌] Error al actualizar en SQL: {e}.")

        elif opcion == '3':
            db_sql.listar_pilotos()          # mostrar IDs antes de pedir transferencia
            db_sql.listar_equipos()
            id_piloto    = int(input("ID del Piloto a transferir: "))
            nuevo_equipo = int(input("ID del nuevo Equipo: "))
            try:
                db_sql.cambiar_piloto_de_equipo(id_piloto, nuevo_equipo)
                hubo_cambios = True
            except Exception as e:
                print(f"  [❌] Error al transferir en SQL: {e}.")

        elif opcion == '4':
            db_sql.listar_pilotos()          # mostrar IDs antes de borrar
            id_piloto = int(input("ID del Piloto a eliminar: "))
            try:
                db_sql.eliminar_piloto(id_piloto)
                hubo_cambios = True
            except Exception as e:
                print(f"  [❌] Error al eliminar en SQL: {e}.")

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
        except Exception as e:
            print(f"\n  [❌] Error al ejecutar la consulta: {e}")
            print(f"       Verificá que la base de datos correspondiente esté activa.")
        
        if opcion != '7': 
            input("\nPresione ENTER para continuar...")

def main():
    mostrar_encabezado()
    
    # 1. Verificar estado de la infraestructura
    verificar_conexiones()
    
    # 2. Asegurar esquema SQL inicial
    print("\nVerificando esquema en la fuente de verdad...")
    db_sql.crear_tablas_f1() 
    
    # 3. Autenticación
    usuario_actual = login_sistema()
    print(f"\n¡Bienvenido {usuario_actual}!")
    
    # 4. Sincronización inicial: SQL → NoSQL
    print("\n[🔄] Preparando sistema de consultas...")
    estado = _sincronizar_en_segundo_plano()
    ok_count = sum(1 for v in estado.values() if v is True)
    print(f"[{'✅' if ok_count == len(estado) else '⚠️'}] Entornos de lectura listos: {ok_count}/{len(estado)}.")
    
    # 5. Flujo de trabajo principal
    menu_principal(usuario_actual)
    
    # 6. Cierre seguro
    db_redis.logout(usuario_actual)
    print("\n¡Sesión finalizada. Hasta luego!")

if __name__ == "__main__":
    main()