import pymssql

# Configuración de conexión al contenedor Docker
config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master' 
}

def obtener_conexion():
    return pymssql.connect(**config)

def testear_sql():
    # Directo al mail con las demas conexiones
    try:
        conn = obtener_conexion()
        conn.close()
        return True, "SQL Server: Conectado"
    except Exception as e:
        return False, f"SQL Server Error: {e}"

def crear_tablas_f1():

    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    print("Conectado exitosamente a SQL Server.")

    # Script SQL con validación IF OBJECT_ID para las 5 tablas maestras
    sql_script = """
    -- 0. Usuarios del sistema (para autenticación con Redis)
    IF OBJECT_ID('dbo.Usuarios', 'U') IS NULL
    BEGIN
        CREATE TABLE Usuarios (
            IdUsuario      INT PRIMARY KEY IDENTITY(1,1),
            Email          VARCHAR(100) NOT NULL UNIQUE,
            Password       VARCHAR(100) NOT NULL,
            NombreCompleto VARCHAR(100) NOT NULL,
            Rol            VARCHAR(50)  NOT NULL
        );
    END

    -- 1. Equipos
    IF OBJECT_ID('dbo.Equipos', 'U') IS NULL
    BEGIN
        CREATE TABLE Equipos (
            IdEquipo INT PRIMARY KEY IDENTITY(1,1),
            Nombre VARCHAR(100) NOT NULL,
            Director VARCHAR(100) NOT NULL,
            Pais VARCHAR(50) NOT NULL
        );
    END

    -- 2. Pilotos 
    IF OBJECT_ID('dbo.Pilotos', 'U') IS NULL
    BEGIN
        CREATE TABLE Pilotos (
            IdPiloto INT PRIMARY KEY IDENTITY(1,1),
            Nombre VARCHAR(100) NOT NULL,
            FechaNacimiento DATE,
            Nacionalidad VARCHAR(50),
            IdEquipo INT FOREIGN KEY REFERENCES Equipos(IdEquipo)
        );
    END

    -- 3. Circuitos 
    IF OBJECT_ID('dbo.Circuitos', 'U') IS NULL
    BEGIN
        CREATE TABLE Circuitos (
            IdCircuito INT PRIMARY KEY IDENTITY(1,1),
            Nombre VARCHAR(100) NOT NULL,
            Ciudad VARCHAR(100) NOT NULL,
            Pais VARCHAR(50) NOT NULL,
            LongitudKM DECIMAL(5,3)
        );
    END

    -- 4. Temporadas 
    IF OBJECT_ID('dbo.Temporadas', 'U') IS NULL
    BEGIN
        CREATE TABLE Temporadas (
            IdTemporada INT PRIMARY KEY IDENTITY(1,1),
            Anio INT NOT NULL UNIQUE
        );
    END

    -- 5. Carreras
    IF OBJECT_ID('dbo.Carreras', 'U') IS NULL
    BEGIN
        CREATE TABLE Carreras (
            IdCarrera INT PRIMARY KEY IDENTITY(1,1),
            Fecha DATE NOT NULL,
            IdCircuito INT FOREIGN KEY REFERENCES Circuitos(IdCircuito),
            IdTemporada INT FOREIGN KEY REFERENCES Temporadas(IdTemporada)
        );
    END

    -- 6. Resultados (sin penalizacion_aplicada — ver DISEÑO.md)
    IF OBJECT_ID('dbo.Resultados', 'U') IS NULL
    BEGIN
        CREATE TABLE Resultados (
            IdPiloto        INT NOT NULL FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            IdCarrera       INT NOT NULL FOREIGN KEY REFERENCES Carreras(IdCarrera),
            PosicionInicial INT NOT NULL,
            PosicionFinal   INT NOT NULL,
            TiempoFinal     VARCHAR(20),
            Puntos          DECIMAL(5,2) NOT NULL DEFAULT 0,
            PRIMARY KEY (IdPiloto, IdCarrera)
        );
    END

    -- 7. PitStops
    IF OBJECT_ID('dbo.PitStops', 'U') IS NULL
    BEGIN
        CREATE TABLE PitStops (
            IdPitStop    INT PRIMARY KEY IDENTITY(1,1),
            IdPiloto     INT NOT NULL FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            IdCarrera    INT NOT NULL FOREIGN KEY REFERENCES Carreras(IdCarrera),
            NumeroParada INT NOT NULL,
            TiempoParada DECIMAL(6,3) NOT NULL
        );
    END

    -- 8. Penalizaciones
    IF OBJECT_ID('dbo.Penalizaciones', 'U') IS NULL
    BEGIN
        CREATE TABLE Penalizaciones (
            IdPenalizacion  INT PRIMARY KEY IDENTITY(1,1),
            IdPiloto        INT NOT NULL FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            IdCarrera       INT NOT NULL FOREIGN KEY REFERENCES Carreras(IdCarrera),
            Tipo            VARCHAR(100) NOT NULL,
            TiempoAdicional DECIMAL(6,3) NOT NULL
        );
    END

    -- 9. Participacion (M:N Pilotos-Temporadas)
    IF OBJECT_ID('dbo.Participacion', 'U') IS NULL
    BEGIN
        CREATE TABLE Participacion (
            IdPiloto    INT NOT NULL FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            IdTemporada INT NOT NULL FOREIGN KEY REFERENCES Temporadas(IdTemporada),
            PRIMARY KEY (IdPiloto, IdTemporada)
        );
    END

    -- 10. Rendimiento (M:N Equipos-Circuitos)
    IF OBJECT_ID('dbo.Rendimiento', 'U') IS NULL
    BEGIN
        CREATE TABLE Rendimiento (
            IdEquipo          INT NOT NULL FOREIGN KEY REFERENCES Equipos(IdEquipo),
            IdCircuito        INT NOT NULL FOREIGN KEY REFERENCES Circuitos(IdCircuito),
            PuntosAcumulados  DECIMAL(8,2) NOT NULL DEFAULT 0,
            MejorPosicion     INT,
            PRIMARY KEY (IdEquipo, IdCircuito)
        );
    END
    """
    cursor.execute(sql_script)
    conn.commit()
    print("Esquema de 10 tablas creado correctamente.")

    # Cerrar conexión
    cursor.close()
    conn.close()
    rellenar_tablas_f1()


def rellenar_tablas_f1():
    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    print("Conectado exitosamente a SQL Server para rellenar tablas.")

    # Insertar datos en las 5 tablas "maestras" de prueba
    insert_script = """
    -- 0. Usuarios del sistema
    IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE Email = 'admin@f1.com')
    BEGIN
        INSERT INTO Usuarios (Email, Password, NombreCompleto, Rol) VALUES
        ('admin@f1.com',    'admin123',  'Administrador F1',   'admin'),
        ('director@f1.com', 'dir456',    'Director de Carrera', 'director'),
        ('prensa@f1.com',   'prensa789', 'Periodista F1',       'prensa');
    END

    -- 1. Equipos
    IF NOT EXISTS (SELECT 1 FROM Equipos WHERE Nombre = 'Red Bull Racing')
    BEGIN
        INSERT INTO Equipos (Nombre, Director, Pais) VALUES 
        ('Red Bull Racing', 'Christian Horner', 'Austria'),
        ('Mercedes AMG', 'Toto Wolff', 'Alemania'),
        ('Ferrari', 'Fred Vasseur', 'Italia'),
        ('McLaren', 'Andrea Stella', 'Reino Unido'),
        ('Alpine', 'Otmar Szafnauer', 'Francia');
    END

    -- 2. Pilotos
    IF NOT EXISTS (SELECT 1 FROM Pilotos WHERE Nombre = 'Max Verstappen')
    BEGIN
        INSERT INTO Pilotos (Nombre, FechaNacimiento, Nacionalidad, IdEquipo) VALUES 
        ('Max Verstappen', '1997-09-30', 'Holanda', 1),
        ('Sergio Perez', '1990-01-26', 'México', 1),
        ('Lewis Hamilton', '1985-01-07', 'Reino Unido', 2),
        ('George Russell', '1998-02-15', 'Reino Unido', 2),
        ('Charles Leclerc', '1997-10-16', 'Mónaco', 3);
    END

    -- 3. Circuitos
    IF NOT EXISTS (SELECT 1 FROM Circuitos WHERE Nombre = 'Monza')
    BEGIN
        INSERT INTO Circuitos (Nombre, Ciudad, Pais, LongitudKM) VALUES 
        ('Monza', 'Monza', 'Italia', 5.793),
        ('Silverstone', 'Silverstone', 'Reino Unido', 5.891),
        ('Spa-Francorchamps', 'Stavelot', 'Bélgica', 7.004),
        ('Suzuka', 'Suzuka', 'Japón', 5.807),
        ('Interlagos', 'São Paulo', 'Brasil', 4.309);
    END

    -- 4. Temporadas
    IF NOT EXISTS (SELECT 1 FROM Temporadas WHERE Anio = 2023)
    BEGIN
        INSERT INTO Temporadas (Anio) VALUES 
        (2023), (2022), (2021), (2020), (2019);
    END

    -- 5. Carreras (5 por temporada, 25 en total para datos históricos 2019-2023)
    IF NOT EXISTS (SELECT 1 FROM Carreras WHERE Fecha = '2023-03-05')
    BEGIN
        INSERT INTO Carreras (Fecha, IdCircuito, IdTemporada) VALUES
        -- 2023 (IdTemporada=1) -> IdCarrera 1-5
        ('2023-03-05', 1, 1),
        ('2023-03-19', 2, 1),
        ('2023-04-02', 3, 1),
        ('2023-04-16', 4, 1),
        ('2023-04-30', 5, 1),
        -- 2022 (IdTemporada=2) -> IdCarrera 6-10
        ('2022-03-06', 1, 2),
        ('2022-03-20', 2, 2),
        ('2022-04-03', 3, 2),
        ('2022-04-17', 4, 2),
        ('2022-05-01', 5, 2),
        -- 2021 (IdTemporada=3) -> IdCarrera 11-15
        ('2021-03-07', 1, 3),
        ('2021-03-21', 2, 3),
        ('2021-04-04', 3, 3),
        ('2021-04-18', 4, 3),
        ('2021-05-02', 5, 3),
        -- 2020 (IdTemporada=4) -> IdCarrera 16-20
        ('2020-07-05', 1, 4),
        ('2020-07-19', 2, 4),
        ('2020-08-02', 3, 4),
        ('2020-08-16', 4, 4),
        ('2020-08-30', 5, 4),
        -- 2019 (IdTemporada=5) -> IdCarrera 21-25
        ('2019-03-17', 1, 5),
        ('2019-03-31', 2, 5),
        ('2019-04-14', 3, 5),
        ('2019-04-28', 4, 5),
        ('2019-05-12', 5, 5);
    END

    -- 6. Resultados (top 3 por carrera, 25 carreras = 75 filas)
    IF NOT EXISTS (SELECT 1 FROM Resultados WHERE IdPiloto = 1 AND IdCarrera = 1)
    BEGIN
        INSERT INTO Resultados (IdPiloto, IdCarrera, PosicionInicial, PosicionFinal, TiempoFinal, Puntos) VALUES
        -- 2023: carreras 1-5. Domina Verstappen (1), Perez (2), Leclerc (5)
        (1, 1, 1, 1, '1:34:00.000', 25), (2, 1, 2, 2, '1:34:11.000', 18), (5, 1, 3, 3, '1:34:22.000', 15),
        (1, 2, 1, 1, '1:20:00.000', 25), (2, 2, 3, 2, '1:20:11.000', 18), (4, 2, 2, 3, '1:20:22.000', 15),
        (1, 3, 1, 1, '1:22:00.000', 25), (5, 3, 2, 2, '1:22:11.000', 18), (3, 3, 3, 3, '1:22:22.000', 15),
        (1, 4, 1, 1, '1:19:00.000', 25), (2, 4, 2, 2, '1:19:11.000', 18), (4, 4, 3, 3, '1:19:22.000', 15),
        (2, 5, 1, 1, '1:21:00.000', 25), (1, 5, 2, 2, '1:21:11.000', 18), (5, 5, 3, 3, '1:21:22.000', 15),
        -- 2022: carreras 6-10. Domina Verstappen (1), Leclerc (5), Perez (2)
        (1, 6, 1, 1, '1:32:00.000', 25), (2, 6, 2, 2, '1:32:11.000', 18), (5, 6, 3, 3, '1:32:22.000', 15),
        (1, 7, 1, 1, '1:24:00.000', 25), (5, 7, 2, 2, '1:24:11.000', 18), (2, 7, 3, 3, '1:24:22.000', 15),
        (1, 8, 1, 1, '1:27:00.000', 25), (2, 8, 2, 2, '1:27:11.000', 18), (4, 8, 3, 3, '1:27:22.000', 15),
        (2, 9, 1, 1, '1:23:00.000', 25), (1, 9, 2, 2, '1:23:11.000', 18), (5, 9, 3, 3, '1:23:22.000', 15),
        (1,10, 1, 1, '1:25:00.000', 25), (2,10, 2, 2, '1:25:11.000', 18), (5,10, 4, 3, '1:25:22.000', 15),
        -- 2021: carreras 11-15. Domina Verstappen (1), Hamilton (3), Perez (2)
        (1,11, 1, 1, '1:29:00.000', 25), (3,11, 2, 2, '1:29:11.000', 18), (2,11, 3, 3, '1:29:22.000', 15),
        (1,12, 1, 1, '1:31:00.000', 25), (2,12, 2, 2, '1:31:11.000', 18), (3,12, 3, 3, '1:31:22.000', 15),
        (1,13, 2, 1, '1:26:00.000', 25), (3,13, 1, 2, '1:26:11.000', 18), (5,13, 3, 3, '1:26:22.000', 15),
        (1,14, 1, 1, '1:28:00.000', 25), (2,14, 3, 2, '1:28:11.000', 18), (3,14, 2, 3, '1:28:22.000', 15),
        (1,15, 1, 1, '1:30:00.000', 25), (3,15, 2, 2, '1:30:11.000', 18), (4,15, 3, 3, '1:30:22.000', 15),
        -- 2020: carreras 16-20. Domina Hamilton (3), Verstappen (1), Russell (4)
        (3,16, 1, 1, '1:33:00.000', 25), (4,16, 2, 2, '1:33:11.000', 18), (1,16, 3, 3, '1:33:22.000', 15),
        (3,17, 1, 1, '1:20:00.000', 25), (1,17, 2, 2, '1:20:11.000', 18), (5,17, 3, 3, '1:20:22.000', 15),
        (3,18, 2, 1, '1:19:00.000', 25), (4,18, 1, 2, '1:19:11.000', 18), (2,18, 3, 3, '1:19:22.000', 15),
        (3,19, 1, 1, '1:21:00.000', 25), (1,19, 2, 2, '1:21:11.000', 18), (5,19, 4, 3, '1:21:22.000', 15),
        (3,20, 1, 1, '1:22:00.000', 25), (4,20, 2, 2, '1:22:11.000', 18), (1,20, 3, 3, '1:22:22.000', 15),
        -- 2019: carreras 21-25. Domina Hamilton (3), Verstappen (1), Leclerc (5)
        (3,21, 1, 1, '1:22:34.000', 25), (4,21, 3, 2, '1:22:45.000', 18), (1,21, 2, 3, '1:22:56.000', 15),
        (3,22, 1, 1, '1:30:12.000', 25), (5,22, 2, 2, '1:30:23.000', 18), (1,22, 4, 3, '1:30:34.000', 15),
        (3,23, 1, 1, '1:25:00.000', 25), (4,23, 2, 2, '1:25:10.000', 18), (2,23, 3, 3, '1:25:20.000', 15),
        (3,24, 1, 1, '1:27:00.000', 25), (1,24, 2, 2, '1:27:11.000', 18), (5,24, 3, 3, '1:27:22.000', 15),
        (3,25, 1, 1, '1:28:00.000', 25), (4,25, 2, 2, '1:28:11.000', 18), (2,25, 3, 3, '1:28:22.000', 15);
    END

    -- 7. PitStops (2 paradas por piloto por carrera, solo carreras 2023)
    IF NOT EXISTS (SELECT 1 FROM PitStops WHERE IdPiloto = 1 AND IdCarrera = 1)
    BEGIN
        INSERT INTO PitStops (IdPiloto, IdCarrera, NumeroParada, TiempoParada) VALUES
        (1,1,1,2.341),(1,1,2,2.198),(2,1,1,2.567),(2,1,2,2.890),(5,1,1,3.102),(5,1,2,2.755),
        (1,2,1,2.210),(1,2,2,2.445),(2,2,1,2.678),(2,2,2,3.001),(4,2,1,2.534),(4,2,2,2.312),
        (1,3,1,2.089),(1,3,2,2.234),(5,3,1,2.891),(5,3,2,3.112),(3,3,1,2.445),(3,3,2,2.678),
        (1,4,1,2.156),(1,4,2,2.390),(2,4,1,2.712),(2,4,2,2.534),(4,4,1,2.867),(4,4,2,3.021),
        (2,5,1,2.334),(2,5,2,2.189),(1,5,1,2.512),(1,5,2,2.745),(5,5,1,2.998),(5,5,2,3.234);
    END

    -- 8. Penalizaciones (algunas carreras 2021-2023)
    IF NOT EXISTS (SELECT 1 FROM Penalizaciones WHERE IdPiloto = 3 AND IdCarrera = 13)
    BEGIN
        INSERT INTO Penalizaciones (IdPiloto, IdCarrera, Tipo, TiempoAdicional) VALUES
        (3, 13, 'Exceder límites de pista', 5.000),
        (2, 22, 'Colisión con otro piloto',  10.000),
        (5, 10, 'Velocidad en pit lane',      5.000);
    END

    -- 9. Participacion (qué piloto corrió en qué temporada)
    IF NOT EXISTS (SELECT 1 FROM Participacion WHERE IdPiloto = 1 AND IdTemporada = 1)
    BEGIN
        INSERT INTO Participacion (IdPiloto, IdTemporada) VALUES
        (1,1),(1,2),(1,3),(1,4),(1,5),
        (2,1),(2,2),(2,3),(2,4),(2,5),
        (3,1),(3,2),(3,3),(3,4),(3,5),
        (4,1),(4,2),(4,3),
        (5,1),(5,2),(5,3),(5,4),(5,5);
    END

    -- 10. Rendimiento (puntos acumulados por equipo en cada circuito)
    IF NOT EXISTS (SELECT 1 FROM Rendimiento WHERE IdEquipo = 1 AND IdCircuito = 1)
    BEGIN
        INSERT INTO Rendimiento (IdEquipo, IdCircuito, PuntosAcumulados, MejorPosicion) VALUES
        (1,1,215,1),(1,2,189,1),(1,3,201,1),(1,4,178,1),(1,5,165,1),
        (2,1,198,1),(2,2,210,1),(2,3,187,2),(2,4,195,1),(2,5,203,1),
        (3,1,120,2),(3,2,105,3),(3,3,132,2),(3,4,118,2),(3,5,140,2);
    END
    """
    # Ejecutar el script completo
    cursor.execute(insert_script)
    conn.commit()
    print("Datos insertados correctamente en todas las tablas.")
    # Cerrar conexión
    cursor.close()
    conn.close()

# ==========================================
# OPERACIONES CRUD PARA SQL
# ==========================================

def insertar_piloto_manual(nombre, fecha_nacimiento, nacionalidad, id_equipo):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        query = "INSERT INTO Pilotos (Nombre, FechaNacimiento, Nacionalidad, IdEquipo) VALUES (%s, %s, %s, %d)"
        cursor.execute(query, (nombre, fecha_nacimiento, nacionalidad, id_equipo))
        conn.commit()
        print(f"Piloto {nombre} registrado con éxito en SQL Server.")
    except Exception as e:
        print(f"Error al insertar piloto: {e}")
    finally:
        conn.close()

# 2. UPDATE 
def actualizar_director_equipo(id_equipo, nuevo_director):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        query = "UPDATE Equipos SET Director = %s WHERE IdEquipo = %d"
        cursor.execute(query, (nuevo_director, id_equipo))
        conn.commit()
        print(f"Equipo ID {id_equipo} actualizado con el nuevo director: {nuevo_director}")
    except Exception as e:
        print(f"Error al actualizar el director: {e}")
    finally:
        conn.close()

def cambiar_piloto_de_equipo(id_piloto, nuevo_id_equipo):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        query = "UPDATE Pilotos SET IdEquipo = %d WHERE IdPiloto = %d"
        cursor.execute(query, (nuevo_id_equipo, id_piloto))
        conn.commit()
        print(f"Piloto ID {id_piloto} transferido al equipo ID {nuevo_id_equipo}")
    except Exception as e:
        print(f"Error al transferir el piloto: {e}")
    finally:
        conn.close()

# 3. DELETE 
def eliminar_piloto(id_piloto):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        query = "DELETE FROM Pilotos WHERE IdPiloto = %d"
        cursor.execute(query, (id_piloto,))
        conn.commit()
        print(f"Piloto ID {id_piloto} eliminado correctamente de SQL Server.")
    except Exception as e:
        print(f"Error al eliminar el piloto: {e}")
    finally:
        conn.close()

# Ejecutar el script completo
crear_tablas_f1()
