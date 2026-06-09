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
    pass  # conexión establecida

    # Script SQL — orden respeta dependencias FK (12 tablas)
    sql_script = """
    -- 1. Equipos (base del modelo, sin dependencias externas)
    IF OBJECT_ID('dbo.Equipos', 'U') IS NULL
    BEGIN
        CREATE TABLE Equipos (
            IdEquipo INT PRIMARY KEY IDENTITY(1,1),
            Nombre VARCHAR(100) NOT NULL,
            Director VARCHAR(100) NOT NULL,
            Pais VARCHAR(50) NOT NULL
        );
    END

    -- 2. Usuarios (IdEquipo nullable: directores tienen equipo asignado)
    IF OBJECT_ID('dbo.Usuarios', 'U') IS NULL
    BEGIN
        CREATE TABLE Usuarios (
            IdUsuario      INT PRIMARY KEY IDENTITY(1,1),
            Email          VARCHAR(100) NOT NULL UNIQUE,
            Password       VARCHAR(100) NOT NULL,
            NombreCompleto VARCHAR(100) NOT NULL,
            Rol            VARCHAR(50)  NOT NULL,
            IdEquipo       INT NULL FOREIGN KEY REFERENCES Equipos(IdEquipo)
        );
    END
    ELSE
    BEGIN
        -- Migración: agrega IdEquipo si la tabla ya existe sin esa columna
        IF NOT EXISTS (
            SELECT 1 FROM sys.columns
            WHERE object_id = OBJECT_ID('dbo.Usuarios') AND name = 'IdEquipo'
        )
            ALTER TABLE Usuarios ADD IdEquipo INT NULL FOREIGN KEY REFERENCES Equipos(IdEquipo);
    END

    -- 3. Auditoria (historial permanente de sesiones; sesión activa vive en Redis)
    IF OBJECT_ID('dbo.Auditoria', 'U') IS NULL
    BEGIN
        CREATE TABLE Auditoria (
            IdAuditoria INT PRIMARY KEY IDENTITY(1,1),
            IdUsuario   INT NOT NULL FOREIGN KEY REFERENCES Usuarios(IdUsuario),
            Accion      VARCHAR(50)  NOT NULL,
            FechaHora   DATETIME     NOT NULL DEFAULT GETDATE()
        );
    END

    -- 4. Pilotos
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

    -- 5. Circuitos
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

    -- 6. Temporadas
    IF OBJECT_ID('dbo.Temporadas', 'U') IS NULL
    BEGIN
        CREATE TABLE Temporadas (
            IdTemporada INT PRIMARY KEY IDENTITY(1,1),
            Anio INT NOT NULL UNIQUE
        );
    END

    -- 7. Carreras
    IF OBJECT_ID('dbo.Carreras', 'U') IS NULL
    BEGIN
        CREATE TABLE Carreras (
            IdCarrera INT PRIMARY KEY IDENTITY(1,1),
            Fecha DATE NOT NULL,
            IdCircuito INT FOREIGN KEY REFERENCES Circuitos(IdCircuito),
            IdTemporada INT FOREIGN KEY REFERENCES Temporadas(IdTemporada)
        );
    END

    -- 8. Resultados (sin penalizacion_aplicada — ver DISEÑO.md)
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

    -- 9. PitStops
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

    -- 10. Penalizaciones
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

    -- 11. Participacion (M:N Pilotos-Temporadas)
    IF OBJECT_ID('dbo.Participacion', 'U') IS NULL
    BEGIN
        CREATE TABLE Participacion (
            IdPiloto    INT NOT NULL FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            IdTemporada INT NOT NULL FOREIGN KEY REFERENCES Temporadas(IdTemporada),
            PRIMARY KEY (IdPiloto, IdTemporada)
        );
    END

    -- 12. Rendimiento (M:N Equipos-Circuitos)
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
    print("Esquema de 12 tablas creado correctamente.")

    # Cerrar conexión
    cursor.close()
    conn.close()
    rellenar_tablas_f1()


def rellenar_tablas_f1():
    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    pass  # conexión establecida

    # Insertar datos en las 12 tablas
    insert_script = """
    -- 1. Equipos (primero, porque Usuarios lo referencia)
    IF NOT EXISTS (SELECT 1 FROM Equipos WHERE Nombre = 'Red Bull Racing')
    BEGIN
        INSERT INTO Equipos (Nombre, Director, Pais) VALUES
        ('Red Bull Racing', 'Christian Horner', 'Austria'),
        ('Mercedes AMG', 'Toto Wolff', 'Alemania'),
        ('Ferrari', 'Fred Vasseur', 'Italia'),
        ('McLaren', 'Andrea Stella', 'Reino Unido'),
        ('Alpine', 'Otmar Szafnauer', 'Francia');
    END

    -- 2. Usuarios (director@f1.com vinculado a Red Bull Racing, IdEquipo=1)
    IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE Email = 'admin@f1.com')
    BEGIN
        INSERT INTO Usuarios (Email, Password, NombreCompleto, Rol, IdEquipo) VALUES
        ('admin@f1.com',    'admin123',  'Administrador F1',    'admin',    NULL),
        ('director@f1.com', 'dir456',    'Director de Carrera', 'director', 1),
        ('prensa@f1.com',   'prensa789', 'Periodista F1',       'prensa',   NULL);
    END

    -- 3. Auditoria — registros de ejemplo de sesiones históricas
    IF NOT EXISTS (SELECT 1 FROM Auditoria WHERE IdUsuario = 1)
    BEGIN
        INSERT INTO Auditoria (IdUsuario, Accion, FechaHora) VALUES
        (1, 'login',  '2024-03-01 09:00:00'),
        (1, 'logout', '2024-03-01 09:45:00'),
        (2, 'login',  '2024-03-01 10:00:00'),
        (2, 'logout', '2024-03-01 10:30:00'),
        (3, 'login',  '2024-03-02 14:00:00'),
        (3, 'expiro', '2024-03-02 14:10:00');
    END

    -- 4. Pilotos
    IF NOT EXISTS (SELECT 1 FROM Pilotos WHERE Nombre = 'Max Verstappen')
    BEGIN
        INSERT INTO Pilotos (Nombre, FechaNacimiento, Nacionalidad, IdEquipo) VALUES 
        ('Max Verstappen', '1997-09-30', 'Holanda', 1),
        ('Sergio Perez', '1990-01-26', 'México', 1),
        ('Lewis Hamilton', '1985-01-07', 'Reino Unido', 2),
        ('George Russell', '1998-02-15', 'Reino Unido', 2),
        ('Charles Leclerc', '1997-10-16', 'Mónaco', 3);
    END

    -- 6. Circuitos
    IF NOT EXISTS (SELECT 1 FROM Circuitos WHERE Nombre = 'Monza')
    BEGIN
        INSERT INTO Circuitos (Nombre, Ciudad, Pais, LongitudKM) VALUES 
        ('Monza', 'Monza', 'Italia', 5.793),
        ('Silverstone', 'Silverstone', 'Reino Unido', 5.891),
        ('Spa-Francorchamps', 'Stavelot', 'Bélgica', 7.004),
        ('Suzuka', 'Suzuka', 'Japón', 5.807),
        ('Interlagos', 'São Paulo', 'Brasil', 4.309);
    END

    -- 7. Temporadas
    IF NOT EXISTS (SELECT 1 FROM Temporadas WHERE Anio = 2023)
    BEGIN
        INSERT INTO Temporadas (Anio) VALUES 
        (2023), (2022), (2021), (2020), (2019);
    END

    -- 8. Carreras (5 por temporada, 25 en total para datos históricos 2019-2023)
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

    -- 9. Resultados (top 3 por carrera, 25 carreras = 75 filas)
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

    -- 10. PitStops (2 paradas por piloto por carrera, solo carreras 2023)
    IF NOT EXISTS (SELECT 1 FROM PitStops WHERE IdPiloto = 1 AND IdCarrera = 1)
    BEGIN
        INSERT INTO PitStops (IdPiloto, IdCarrera, NumeroParada, TiempoParada) VALUES
        (1,1,1,2.341),(1,1,2,2.198),(2,1,1,2.567),(2,1,2,2.890),(5,1,1,3.102),(5,1,2,2.755),
        (1,2,1,2.210),(1,2,2,2.445),(2,2,1,2.678),(2,2,2,3.001),(4,2,1,2.534),(4,2,2,2.312),
        (1,3,1,2.089),(1,3,2,2.234),(5,3,1,2.891),(5,3,2,3.112),(3,3,1,2.445),(3,3,2,2.678),
        (1,4,1,2.156),(1,4,2,2.390),(2,4,1,2.712),(2,4,2,2.534),(4,4,1,2.867),(4,4,2,3.021),
        (2,5,1,2.334),(2,5,2,2.189),(1,5,1,2.512),(1,5,2,2.745),(5,5,1,2.998),(5,5,2,3.234);
    END

    -- 11. Penalizaciones (algunas carreras 2021-2023)
    IF NOT EXISTS (SELECT 1 FROM Penalizaciones WHERE IdPiloto = 3 AND IdCarrera = 13)
    BEGIN
        INSERT INTO Penalizaciones (IdPiloto, IdCarrera, Tipo, TiempoAdicional) VALUES
        (3, 13, 'Exceder límites de pista', 5.000),
        (2, 22, 'Colisión con otro piloto',  10.000),
        (5, 10, 'Velocidad en pit lane',      5.000);
    END

    -- 12. Participacion (qué piloto corrió en qué temporada)
    IF NOT EXISTS (SELECT 1 FROM Participacion WHERE IdPiloto = 1 AND IdTemporada = 1)
    BEGIN
        INSERT INTO Participacion (IdPiloto, IdTemporada) VALUES
        (1,1),(1,2),(1,3),(1,4),(1,5),
        (2,1),(2,2),(2,3),(2,4),(2,5),
        (3,1),(3,2),(3,3),(3,4),(3,5),
        (4,1),(4,2),(4,3),
        (5,1),(5,2),(5,3),(5,4),(5,5);
    END

    -- 13. Rendimiento (puntos acumulados por equipo en cada circuito)
    IF NOT EXISTS (SELECT 1 FROM Rendimiento WHERE IdEquipo = 1 AND IdCircuito = 1)
    BEGIN
        INSERT INTO Rendimiento (IdEquipo, IdCircuito, PuntosAcumulados, MejorPosicion) VALUES
        (1,1,215,1),(1,2,189,1),(1,3,201,1),(1,4,178,1),(1,5,165,1),
        (2,1,198,1),(2,2,210,1),(2,3,187,2),(2,4,195,1),(2,5,203,1),
        (3,1,120,2),(3,2,105,3),(3,3,132,2),(3,4,118,2),(3,5,140,2);
    END

    -- =====================================================================
    -- DATOS ADICIONALES: Temporadas 2016-2018
    -- Necesarios para que CU5 (>10 podios Y >5 temporadas) devuelva resultados
    -- Con solo 5 temporadas (2019-2023) ningun piloto supera el umbral de >5
    -- =====================================================================

    IF NOT EXISTS (SELECT 1 FROM Temporadas WHERE Anio = 2018)
    BEGIN
        INSERT INTO Temporadas (Anio) VALUES (2018), (2017), (2016);
    END

    -- Carreras 2018 (IdTemporada=6) -> IdCarrera 26-30
    -- Carreras 2017 (IdTemporada=7) -> IdCarrera 31-35
    -- Carreras 2016 (IdTemporada=8) -> IdCarrera 36-40
    IF NOT EXISTS (SELECT 1 FROM Carreras WHERE Fecha = '2018-03-25')
    BEGIN
        INSERT INTO Carreras (Fecha, IdCircuito, IdTemporada) VALUES
        ('2018-03-25', 1, 6), ('2018-04-08', 2, 6), ('2018-04-29', 3, 6), ('2018-05-13', 4, 6), ('2018-05-27', 5, 6),
        ('2017-03-26', 1, 7), ('2017-04-09', 2, 7), ('2017-04-30', 3, 7), ('2017-05-14', 4, 7), ('2017-05-28', 5, 7),
        ('2016-03-20', 1, 8), ('2016-04-03', 2, 8), ('2016-04-24', 3, 8), ('2016-05-08', 4, 8), ('2016-05-29', 5, 8);
    END

    -- Resultados 2016-2018 (45 filas, top 3 por carrera)
    -- 2018: Hamilton (3) gana 4, Verstappen (1) gana 1. Leclerc (5) completa los podios (debut en Sauber).
    -- 2017: Hamilton (3) gana 4, Verstappen (1) gana 1. Russell (4) completa los podios.
    -- 2016: Hamilton (3) gana 3, Verstappen (1) gana 2. Russell (4) completa los podios.
    IF NOT EXISTS (SELECT 1 FROM Resultados WHERE IdPiloto = 3 AND IdCarrera = 26)
    BEGIN
        INSERT INTO Resultados (IdPiloto, IdCarrera, PosicionInicial, PosicionFinal, TiempoFinal, Puntos) VALUES
        -- 2018: carreras 26-30
        (3,26,1,1,'1:34:00.000',25), (1,26,2,2,'1:34:11.000',18), (5,26,3,3,'1:34:22.000',15),
        (3,27,1,1,'1:35:00.000',25), (1,27,2,2,'1:35:11.000',18), (5,27,3,3,'1:35:22.000',15),
        (1,28,1,1,'1:33:00.000',25), (3,28,2,2,'1:33:11.000',18), (5,28,3,3,'1:33:22.000',15),
        (3,29,1,1,'1:36:00.000',25), (1,29,2,2,'1:36:11.000',18), (5,29,3,3,'1:36:22.000',15),
        (3,30,1,1,'1:32:00.000',25), (1,30,2,2,'1:32:11.000',18), (5,30,3,3,'1:32:22.000',15),
        -- 2017: carreras 31-35
        (3,31,1,1,'1:35:00.000',25), (1,31,2,2,'1:35:11.000',18), (4,31,3,3,'1:35:22.000',15),
        (3,32,1,1,'1:36:00.000',25), (1,32,2,2,'1:36:11.000',18), (4,32,3,3,'1:36:22.000',15),
        (1,33,1,1,'1:34:00.000',25), (3,33,2,2,'1:34:11.000',18), (4,33,3,3,'1:34:22.000',15),
        (3,34,1,1,'1:37:00.000',25), (1,34,2,2,'1:37:11.000',18), (4,34,3,3,'1:37:22.000',15),
        (3,35,1,1,'1:33:00.000',25), (1,35,2,2,'1:33:11.000',18), (4,35,3,3,'1:33:22.000',15),
        -- 2016: carreras 36-40
        (3,36,1,1,'1:36:00.000',25), (1,36,2,2,'1:36:11.000',18), (4,36,3,3,'1:36:22.000',15),
        (3,37,1,1,'1:37:00.000',25), (1,37,2,2,'1:37:11.000',18), (4,37,3,3,'1:37:22.000',15),
        (1,38,1,1,'1:35:00.000',25), (3,38,2,2,'1:35:11.000',18), (4,38,3,3,'1:35:22.000',15),
        (3,39,1,1,'1:38:00.000',25), (1,39,2,2,'1:38:11.000',18), (4,39,3,3,'1:38:22.000',15),
        (1,40,1,1,'1:34:00.000',25), (3,40,2,2,'1:34:11.000',18), (4,40,3,3,'1:34:22.000',15);
    END

    -- Participacion para 2016-2018
    IF NOT EXISTS (SELECT 1 FROM Participacion WHERE IdPiloto = 1 AND IdTemporada = 6)
    BEGIN
        INSERT INTO Participacion (IdPiloto, IdTemporada) VALUES
        (1,6),(1,7),(1,8),   -- Verstappen
        (3,6),(3,7),(3,8),   -- Hamilton
        (4,6),(4,7),(4,8),   -- Russell
        (5,6);               -- Leclerc (temporada debut 2018)
    END

    -- =====================================================================
    -- TEMPORADAS 2024-2026: solo carreras, sin resultados
    -- Disponibles para demo del CRUD (insertar resultados frescos)
    -- =====================================================================

    IF NOT EXISTS (SELECT 1 FROM Temporadas WHERE Anio = 2024)
    BEGIN
        INSERT INTO Temporadas (Anio) VALUES (2024), (2025), (2026);
    END

    -- Carreras 2024 (IdTemporada=9) -> IdCarrera 41-45
    -- Carreras 2025 (IdTemporada=10) -> IdCarrera 46-50
    -- Carreras 2026 (IdTemporada=11) -> IdCarrera 51-55
    IF NOT EXISTS (SELECT 1 FROM Carreras WHERE Fecha = '2024-03-02')
    BEGIN
        INSERT INTO Carreras (Fecha, IdCircuito, IdTemporada) VALUES
        ('2024-03-02', 1, 9),  ('2024-03-16', 2, 9),  ('2024-04-06', 3, 9),  ('2024-04-20', 4, 9),  ('2024-05-04', 5, 9),
        ('2025-03-01', 1, 10), ('2025-03-15', 2, 10), ('2025-04-05', 3, 10), ('2025-04-19', 4, 10), ('2025-05-03', 5, 10),
        ('2026-03-07', 1, 11), ('2026-03-21', 2, 11), ('2026-04-11', 3, 11), ('2026-04-25', 4, 11), ('2026-05-09', 5, 11);
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
        cursor.execute(
            "INSERT INTO Pilotos (Nombre, FechaNacimiento, Nacionalidad, IdEquipo) VALUES (%s, %s, %s, %d)",
            (nombre, fecha_nacimiento, nacionalidad, id_equipo)
        )
        conn.commit()
        print(f"  Piloto '{nombre}' registrado en SQL Server.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 2. UPDATE
def actualizar_director_equipo(id_equipo, nuevo_director):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Equipos SET Director = %s WHERE IdEquipo = %d",
            (nuevo_director, id_equipo)
        )
        conn.commit()
        print(f"  Equipo ID {id_equipo} actualizado — nuevo director: {nuevo_director}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def cambiar_piloto_de_equipo(id_piloto, nuevo_id_equipo):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Pilotos SET IdEquipo = %d WHERE IdPiloto = %d",
            (nuevo_id_equipo, id_piloto)
        )
        conn.commit()
        print(f"  Piloto ID {id_piloto} transferido al equipo ID {nuevo_id_equipo}.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 3. READ
def listar_pilotos():
    """
    Devuelve y muestra todos los pilotos actuales con su equipo.
    Útil para saber los IDs antes de hacer una transferencia o eliminación.
    """
    conn = pymssql.connect(**config)
    cursor = conn.cursor(as_dict=True)
    try:
        cursor.execute("""
            SELECT p.IdPiloto, p.Nombre, p.Nacionalidad, p.FechaNacimiento, e.Nombre AS Equipo
            FROM Pilotos p
            JOIN Equipos e ON p.IdEquipo = e.IdEquipo
            ORDER BY p.IdPiloto
        """)
        pilotos = cursor.fetchall()
        sep = "─" * 50
        print(f"\n{sep}")
        print(f" Pilotos registrados  [SQL Server]")
        print(sep)
        for p in pilotos:
            print(f"  ID {p['IdPiloto']:>2} | {p['Nombre']:<25} | {p['Nacionalidad']:<15} | {p['Equipo']}")
        return pilotos
    except Exception as e:
        print(f"Error al listar pilotos: {e}")
        return []
    finally:
        conn.close()

def listar_equipos():
    """
    Devuelve y muestra todos los equipos con su director.
    Útil para saber los IDs antes de hacer una transferencia.
    """
    conn = pymssql.connect(**config)
    cursor = conn.cursor(as_dict=True)
    try:
        cursor.execute("SELECT IdEquipo, Nombre, Director FROM Equipos ORDER BY IdEquipo")
        equipos = cursor.fetchall()
        sep = "─" * 50
        print(f"\n{sep}")
        print(f" Equipos registrados  [SQL Server]")
        print(sep)
        for e in equipos:
            print(f"  ID {e['IdEquipo']} | {e['Nombre']:<25} | Director: {e['Director']}")
        return equipos
    except Exception as e:
        print(f"Error al listar equipos: {e}")
        return []
    finally:
        conn.close()

# 4. DELETE
def eliminar_piloto(id_piloto):
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Pilotos WHERE IdPiloto = %d", (id_piloto,))
        conn.commit()
        print(f"  Piloto ID {id_piloto} eliminado de SQL Server.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_carreras():
    """Devuelve y muestra todas las carreras con su circuito y año, ordenadas por año desc."""
    conn = pymssql.connect(**config)
    cursor = conn.cursor(as_dict=True)
    try:
        cursor.execute("""
            SELECT c.IdCarrera, c.Fecha, ci.Nombre AS Circuito, t.Anio
            FROM Carreras c
            JOIN Circuitos  ci ON c.IdCircuito  = ci.IdCircuito
            JOIN Temporadas t  ON c.IdTemporada = t.IdTemporada
            ORDER BY t.Anio DESC, c.IdCarrera ASC
        """)
        carreras = cursor.fetchall()
        sep = "─" * 50
        print(f"\n{sep}")
        print(f" Carreras registradas  [SQL Server]")
        print(sep)
        for c in carreras:
            print(f"  ID {c['IdCarrera']:>2} | {c['Anio']} | {str(c['Fecha'])[:10]} | {c['Circuito']}")
        return carreras
    except Exception as e:
        print(f"Error al listar carreras: {e}")
        return []
    finally:
        conn.close()


def listar_resultados():
    """Muestra todos los resultados existentes agrupados por carrera."""
    conn = pymssql.connect(**config)
    cursor = conn.cursor(as_dict=True)
    try:
        cursor.execute("""
            SELECT r.IdPiloto, r.IdCarrera, p.Nombre AS Piloto, e.Nombre AS Equipo,
                   r.PosicionFinal, t.Anio, ci.Nombre AS Circuito
            FROM Resultados r
            JOIN Pilotos    p  ON r.IdPiloto   = p.IdPiloto
            JOIN Equipos    e  ON p.IdEquipo   = e.IdEquipo
            JOIN Carreras   c  ON r.IdCarrera  = c.IdCarrera
            JOIN Circuitos  ci ON c.IdCircuito = ci.IdCircuito
            JOIN Temporadas t  ON c.IdTemporada = t.IdTemporada
            ORDER BY t.Anio DESC, r.IdCarrera, r.PosicionFinal
        """)
        rows = cursor.fetchall()
        sep = "─" * 60
        print(f"\n{sep}")
        print(f" Resultados registrados  [SQL Server]")
        print(sep)
        carrera_actual = None
        for r in rows:
            if r['IdCarrera'] != carrera_actual:
                carrera_actual = r['IdCarrera']
                print(f"\n  Carrera ID {r['IdCarrera']} — {r['Anio']} {r['Circuito']}")
            print(f"    P{r['PosicionFinal']} | Piloto ID {r['IdPiloto']:>2} | {r['Piloto']:<25} | {r['Equipo']}")
        return rows
    except Exception as e:
        print(f"Error al listar resultados: {e}")
        return []
    finally:
        conn.close()


def listar_pit_stops():
    """Muestra todos los pit stops existentes agrupados por carrera y piloto."""
    conn = pymssql.connect(**config)
    cursor = conn.cursor(as_dict=True)
    try:
        cursor.execute("""
            SELECT ps.IdPiloto, ps.IdCarrera, ps.NumeroParada, ps.TiempoParada,
                   p.Nombre AS Piloto, t.Anio, ci.Nombre AS Circuito
            FROM PitStops ps
            JOIN Pilotos    p  ON ps.IdPiloto  = p.IdPiloto
            JOIN Carreras   c  ON ps.IdCarrera = c.IdCarrera
            JOIN Circuitos  ci ON c.IdCircuito = ci.IdCircuito
            JOIN Temporadas t  ON c.IdTemporada = t.IdTemporada
            ORDER BY t.Anio DESC, ps.IdCarrera, ps.IdPiloto, ps.NumeroParada
        """)
        rows = cursor.fetchall()
        sep = "─" * 60
        print(f"\n{sep}")
        print(f" Pit stops registrados  [SQL Server]")
        print(sep)
        clave_actual = None
        for r in rows:
            clave = (r['IdCarrera'], r['IdPiloto'])
            if clave != clave_actual:
                clave_actual = clave
                print(f"\n  Carrera ID {r['IdCarrera']} ({r['Anio']} {r['Circuito']}) — Piloto ID {r['IdPiloto']} {r['Piloto']}")
            print(f"    Parada #{r['NumeroParada']} | {r['TiempoParada']}s")
        return rows
    except Exception as e:
        print(f"Error al listar pit stops: {e}")
        return []
    finally:
        conn.close()


def insertar_resultado(id_piloto, id_carrera, posicion_final, puntos):
    """
    Inserta un resultado en Resultados (fuente de verdad).
    Después del sync: visible en CU2 (si pos=1), CU3 (si pos=1), CU5 (si pos<=3).
    """
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Resultados (IdPiloto, IdCarrera, PosicionInicial, PosicionFinal, TiempoFinal, Puntos) "
            "VALUES (%d, %d, %d, %d, %s, %s)",
            (id_piloto, id_carrera, posicion_final, posicion_final, "1:30:00.000", puntos)
        )
        conn.commit()
        print(f"  Resultado registrado: Piloto ID {id_piloto}, Carrera ID {id_carrera}, P{posicion_final} ({puntos} pts).")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def eliminar_resultado(id_piloto, id_carrera):
    """Elimina un resultado de Resultados. Retorna True si se eliminó, False si no existía."""
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM Resultados WHERE IdPiloto = %d AND IdCarrera = %d",
            (id_piloto, id_carrera)
        )
        conn.commit()
        if cursor.rowcount == 0:
            print(f"  No existe resultado para Piloto ID {id_piloto} en Carrera ID {id_carrera}.")
            return False
        print(f"  Resultado eliminado: Piloto ID {id_piloto}, Carrera ID {id_carrera}.")
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insertar_pit_stop_sql(id_piloto, id_carrera, numero_parada, tiempo_parada):
    """Inserta un pit stop en PitStops. Después del sync: visible en CU4."""
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO PitStops (IdPiloto, IdCarrera, NumeroParada, TiempoParada) VALUES (%d, %d, %d, %s)",
            (id_piloto, id_carrera, numero_parada, tiempo_parada)
        )
        conn.commit()
        print(f"  Pit stop #{numero_parada} registrado: Piloto ID {id_piloto}, Carrera ID {id_carrera}.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def eliminar_pit_stops_piloto(id_piloto, id_carrera):
    """Elimina todos los pit stops de un piloto en una carrera. Retorna True si se eliminó algo."""
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM PitStops WHERE IdPiloto = %d AND IdCarrera = %d",
            (id_piloto, id_carrera)
        )
        conn.commit()
        if cursor.rowcount == 0:
            print(f"  No existen pit stops para Piloto ID {id_piloto} en Carrera ID {id_carrera}.")
            return False
        print(f"  {cursor.rowcount} pit stop(s) eliminados: Piloto ID {id_piloto}, Carrera ID {id_carrera}.")
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# Ejecutar el script completo solo cuando se corre directamente (no al importar)
if __name__ == "__main__":
    crear_tablas_f1()
