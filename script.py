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

    # Script SQL con validación IF OBJECT_ID para las 5 tablas maestras
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
    """
    cursor.execute(sql_script)
    conn.commit()
    print("Esquema de 5 tablas maestras creado correctamente.")

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