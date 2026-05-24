import sys
import time

# Importamos los módulos
import db_sql
import db_redis
import db_cassandra
import db_mongo
import db_neo4j

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
        print("  ✅ SQL Server: Conectado")
    except Exception as e:
        print(f"  ❌ SQL Server: Error de conexión -> {e}")

    # 2. Redis
    try:
        db_redis.r.ping()
        print("  ✅ Redis: Conectado")
    except Exception as e:
        print(f"  ❌ Redis: Error de conexión -> {e}")

    # 3. Cassandra
    try:
        db_cassandra.session.execute("SELECT release_version FROM system.local")
        print("  ✅ Cassandra: Conectado")
    except Exception as e:
        print(f"  ❌ Cassandra: Error de conexión -> {e}")

    # 4. MongoDB
    try:
        db_mongo.mongo_client.admin.command('ping')
        print("  ✅ MongoDB: Conectado")
    except Exception as e:
        print(f"  ❌ MongoDB: Error de conexión -> {e}")

    # 5. Neo4j
    try:
        db_neo4j.driver.verify_connectivity()
        print("  ✅ Neo4j: Conectado")
    except Exception as e:
        print(f"  ❌ Neo4j: Error de conexión -> {e}")
        
    print("-" * 60)

def login_sistema():
    """Maneja la autenticación usando SQL (validación) y Redis (sesión)."""
    intentos = 3
    while intentos > 0:
        email = input("\nEmail: ")
        password = input("Contraseña: ")
        
        # Validar en SQL y generar sesión en Redis
        ttl = db_redis.login(email, password, dispositivo_confiable=True)
        
        if ttl:
            return email
        else:
            intentos -= 1
            print(f"Credenciales inválidas. Intentos restantes: {intentos}")
    
    print("\nAcceso bloqueado. Cerrando sistema.")
    sys.exit()

def _sincronizar_en_segundo_plano():
    """
    Función interna e invisible. 
    Transfiere los datos desde SQL a las bases NoSQL automáticamente.
    """
    # Cassandra
    db_cassandra.crear_keyspace_y_tablas()
    db_cassandra.insertar_datos()
    
    # MongoDB
    db_mongo.crear_colecciones_e_indices()
    db_mongo.insertar_datos()
    
    # Neo4j
    # db_neo4j.borrarDatosNeo4j()
    # db_neo4j.poblar_desde_sql() 

def menu_crud():
    """Submenú para manejar las operaciones CRUD en la fuente de verdad."""
    while True:
        print("\n" + "-"*40)
        print("      GESTIÓN DE DATOS (CRUD)      ")
        print("-" + "-"*40)
        print("1. Insertar nuevo Piloto")
        print("2. Actualizar Director de Equipo")
        print("3. Cambiar Piloto de Equipo (Transferencia)")
        print("4. Eliminar Piloto")
        print("0. Volver al menú principal")
        
        opcion = input("\nSeleccione una operación: ")
        
        # Bandera para saber si hubo cambios en la DB
        hubo_cambios = False
        
        if opcion == '1':
            nombre = input("Nombre del piloto: ")
            fecha = input("Fecha de nacimiento (YYYY-MM-DD): ")
            nac = input("Nacionalidad: ")
            id_equipo = int(input("ID del Equipo: "))
            db_sql.insertar_piloto_manual(nombre, fecha, nac, id_equipo)
            hubo_cambios = True
            
        elif opcion == '2':
            id_equipo = int(input("ID del Equipo a modificar: "))
            nuevo_dir = input("Nombre del nuevo Director: ")
            db_sql.actualizar_director_equipo(id_equipo, nuevo_dir)
            hubo_cambios = True
            
        elif opcion == '3':
            id_piloto = int(input("ID del Piloto a transferir: "))
            nuevo_equipo = int(input("ID del nuevo Equipo: "))
            db_sql.cambiar_piloto_de_equipo(id_piloto, nuevo_equipo)
            hubo_cambios = True
            
        elif opcion == '4':
            id_piloto = int(input("ID del Piloto a eliminar: "))
            db_sql.eliminar_piloto(id_piloto)
            hubo_cambios = True
            
        elif opcion == '0':
            break
        else:
            print("Opción no válida.")
        
        # Disparamos la transferencia de datos automáticamente si algo se modificó
        if hubo_cambios:
            print("[🔄] Actualizando entornos de lectura en segundo plano...")
            _sincronizar_en_segundo_plano()
            print("[✅] Sistema actualizado.")

def menu_principal():
    while True:
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
            print("\nRanking de Países con más carreras:")
            db_neo4j.paisConMasCarreras()
            print("\nPaíses con más de 1 circuito:")
            db_neo4j.paisConMas1Circuito()
        elif opcion == '7':
            menu_crud()
        elif opcion == '8':
            db_redis.sesiones_activas()
        elif opcion == '0':
            break
        else:
            print("Opción no válida. Intente nuevamente.")
        
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
    
    # 4. Sincronización inicial silenciosa al arrancar
    print("[🔄] Preparando sistema de consultas...")
    _sincronizar_en_segundo_plano()
    
    # 5. Flujo de trabajo principal
    menu_principal()
    
    # 6. Cierre seguro
    db_redis.logout(usuario_actual)
    print("\n¡Sesión finalizada. Hasta luego!")

if __name__ == "__main__":
    main()