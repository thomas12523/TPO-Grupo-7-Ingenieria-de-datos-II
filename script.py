import pymssql
import datosRellenoSQL as dSQL

# Configuración de conexión al contenedor Docker
config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master' 
}

def crear_tablas_f1():

    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    print("Conectado exitosamente a SQL Server.")

    # Script SQL con validación IF OBJECT_ID para las 10 tablas
    sql_script = """
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

    -- 6. Resultados 
    IF OBJECT_ID('dbo.Resultados', 'U') IS NULL
    BEGIN
        CREATE TABLE Resultados (
            IdResultado INT PRIMARY KEY IDENTITY(1,1),
            IdCarrera INT FOREIGN KEY REFERENCES Carreras(IdCarrera),
            IdPiloto INT FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            PosicionInicial INT,
            PosicionFinal INT,
            TiempoFinal VARCHAR(20),
            PuntosGanados INT,
            PenalizacionAplicada BIT DEFAULT 0
        );
    END

    -- 7. PitStops 
    IF OBJECT_ID('dbo.PitStops', 'U') IS NULL
    BEGIN
        CREATE TABLE PitStops (
            IdPitStop INT PRIMARY KEY IDENTITY(1,1),
            IdCarrera INT FOREIGN KEY REFERENCES Carreras(IdCarrera),
            IdPiloto INT FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            NumeroParada INT,
            TiempoParada DECIMAL(5,3)
        );
    END

    -- 8. Penalizaciones 
    IF OBJECT_ID('dbo.Penalizaciones', 'U') IS NULL
    BEGIN
        CREATE TABLE Penalizaciones (
            IdPenalizacion INT PRIMARY KEY IDENTITY(1,1),
            IdCarrera INT FOREIGN KEY REFERENCES Carreras(IdCarrera),
            IdPiloto INT FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            TipoPenalizacion VARCHAR(100),
            TiempoAdicional DECIMAL(5,2)
        );
    END

    -- 9. participaciones (Relación N:N) 
    IF OBJECT_ID('dbo.participaciones', 'U') IS NULL
    BEGIN
        CREATE TABLE participaciones (
            IdPiloto INT FOREIGN KEY REFERENCES Pilotos(IdPiloto),
            IdTemporada INT FOREIGN KEY REFERENCES Temporadas(IdTemporada),
            PRIMARY KEY (IdPiloto, IdTemporada)
        );
    END

    -- 10. rendimientos (Relación N:N) 
    IF OBJECT_ID('dbo.rendimientos', 'U') IS NULL
    BEGIN
        CREATE TABLE rendimientos (
            IdEquipo INT FOREIGN KEY REFERENCES Equipos(IdEquipo),
            IdCircuito INT FOREIGN KEY REFERENCES Circuitos(IdCircuito),
            MejorTiempoCarrera VARCHAR(20),
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

def rellenarBD():
    dSQL.rellenar_tablas_f1()
 
def verificar_datos():
    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    print("Conectado exitosamente a SQL Server para verificar datos.")

    # Consultar datos de la tabla Equipos
    print("\nDatos de la tabla Equipos:")
    cursor.execute("SELECT * FROM Equipos")
    equipos = cursor.fetchall()
    for equipo in equipos:
        print(equipo)

    # Consultar datos de la tabla Pilotos
    print("\nDatos de la tabla Pilotos:")
    cursor.execute("SELECT * FROM Pilotos")
    pilotos = cursor.fetchall()
    for piloto in pilotos:
        print(piloto)

    # Consultar datos de la tabla Circuitos
    print("\nDatos de la tabla Circuitos:")
    cursor.execute("SELECT * FROM Circuitos")
    circuitos = cursor.fetchall()
    for circuito in circuitos:
        print(circuito)

    # Cerrar conexión
    cursor.close()
    conn.close()
    print("\nVerificación de datos completada.")

# Ejecutar el script completo
crear_tablas_f1()
rellenarBD()
verificar_datos()