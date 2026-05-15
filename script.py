import pymssql

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
    rellenar_tablas_f1()

 
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

def rellenar_tablas_f1():
    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    print("Conectado exitosamente a SQL Server para rellenar tablas.")

    # Insertar datos únicamente en las 5 tablas maestras (Arquitectura Políglota)
    insert_script = """
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

    -- 5. Carreras
    IF NOT EXISTS (SELECT 1 FROM Carreras WHERE Fecha = '2023-03-05')
    BEGIN
        INSERT INTO Carreras (Fecha, IdCircuito, IdTemporada) VALUES 
        ('2023-03-05', 1, 1),
        ('2023-03-19', 2, 1),
        ('2023-04-02', 3, 1),
        ('2023-04-16', 4, 1),
        ('2023-04-30', 5, 1);
    END
    """

    # Ejecutar el script completo
    cursor.execute(insert_script)
    conn.commit()
    print("Datos maestros insertados correctamente en las tablas.")

    # Cerrar conexión
    cursor.close()
    conn.close()
# Ejecutar el script completo
crear_tablas_f1()
verificar_datos()