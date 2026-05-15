import pymssql
config = {
    'server': 'localhost',
    'user': 'sa',
    'password': 'Password123!',
    'database': 'master' 
}
def rellenar_tablas_f1():
    # Establecer conexión
    conn = pymssql.connect(**config)
    cursor = conn.cursor()
    print("Conectado exitosamente a SQL Server para rellenar tablas.")

    # Insertar datos en las tablas
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

    -- 6. Resultados
    IF NOT EXISTS (SELECT 1 FROM Resultados WHERE IdCarrera = 1 AND IdPiloto = 1)
    BEGIN
        INSERT INTO Resultados (IdCarrera, IdPiloto, PosicionInicial, PosicionFinal, TiempoFinal, PuntosGanados, PenalizacionAplicada) VALUES 
        (1, 1, 1, 1, '1:30:45', 25, 0),
        (1, 2, 2, 2, '1:31:10', 18, 0),
        (1, 3, 3, 3, '1:31:30', 15, 0),
        (2, 1, 1, 1, '1:28:50', 25, 0),
        (2, 2, 2, 2, '1:29:15', 18, 0);
    END

    -- 7. PitStops
    IF NOT EXISTS (SELECT 1 FROM PitStops WHERE IdCarrera = 1 AND IdPiloto = 1)
    BEGIN
        INSERT INTO PitStops (IdCarrera, IdPiloto, NumeroParada, TiempoParada) VALUES 
        (1, 1, 1, 2.5),
        (1, 2, 1, 2.7),
        (1, 3, 1, 2.6),
        (2, 1, 1, 2.4),
        (2, 2, 1, 2.8);
    END

    -- 8. Penalizaciones
    IF NOT EXISTS (SELECT 1 FROM Penalizaciones WHERE IdCarrera = 1 AND IdPiloto = 3)
    BEGIN
        INSERT INTO Penalizaciones (IdCarrera, IdPiloto, TipoPenalizacion, TiempoAdicional) VALUES 
        (1, 3, 'Exceso de velocidad en pits', 5.0),
        (2, 2, 'Colisión', 10.0);
    END

    -- 9. Participaciones
    IF NOT EXISTS (SELECT 1 FROM participaciones WHERE IdPiloto = 1 AND IdTemporada = 1)
    BEGIN
        INSERT INTO participaciones (IdPiloto, IdTemporada) VALUES 
        (1, 1), (2, 1), (3, 1), (4, 1), (5, 1);
    END

    -- 10. Rendimientos
    IF NOT EXISTS (SELECT 1 FROM rendimientos WHERE IdEquipo = 1 AND IdCircuito = 1)
    BEGIN
        INSERT INTO rendimientos (IdEquipo, IdCircuito, MejorTiempoCarrera) VALUES 
        (1, 1, '1:30:45'),
        (2, 2, '1:28:50'),
        (3, 3, '1:31:30'),
        (4, 4, '1:32:00'),
        (5, 5, '1:33:15');
    END
    """

    # Ejecutar el script completo
    cursor.execute(insert_script)
    conn.commit()
    print("Datos insertados correctamente en las tablas.")

    # Cerrar conexión
    cursor.close()
    conn.close()