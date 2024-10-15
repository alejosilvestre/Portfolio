-- Creamos BBDD donde almacenar la info de las tablas
CREATE DATABASE iubenda;
USE iubenda;

-- Creamos Tabla users,subscriptions y subscriptions_renewals --
CREATE TABLE users(
	id int PRIMARY KEY,
    created_at DATETIME,
    country_code VARCHAR(255)
);

CREATE TABLE subscriptions(
	id INT PRIMARY KEY,
    user_id INT,
    product_family varchar(255),
    license_type varchar(255),
    period varchar(255),
    start_at DATETIME,
    end_at DATETIME, 
    renewals_count INT, 
    currency VARCHAR(8),
    total_eur decimal(10,2),
    total_usd decimal(10,2),
    net_eur decimal(10,2),
    net_usd decimal(10,2),
    exchange_rate decimal(10,8),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE subscriptions_renewals(
	id INT PRIMARY KEY,
    renewed_id INT,
    start_at DATETIME,
    end_at DATETIME,
    currency VARCHAR(8),
    total_eur DECIMAL(10,2),
    total_usd DECIMAL(10,2),
    net_eur DECIMAL(10,2),
    net_usd DECIMAL(10,2),
    exchange_rate DECIMAL(10,8),
    FOREIGN KEY (renewed_id) REFERENCES subscriptions(id)
);

-- Buscamos carpeta segura desde donde la cual volcar los datos a MySQL --

SHOW VARIABLES LIKE 'secure_file_priv';

-- Volcamos datos de los csv creados y limpios a las tablas creadas y revisamos cada volcado --

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/users.csv'
INTO TABLE users
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id, created_at, country_code);

SELECT * FROM users LIMIT 10;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/subscriptions.csv'
INTO TABLE subscriptions
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id, user_id, product_family, license_type, period, start_at,
 end_at, renewals_count, currency, total_eur, total_usd, net_eur, net_usd, exchange_rate);

SELECT * FROM subscriptions LIMIT 10;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/subscriptions_renewals.csv'
INTO TABLE subscriptions_renewals 
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(id, renewed_id, start_at, end_at, currency, total_eur, total_usd, net_eur, net_usd, exchange_rate);

SELECT * FROM subscriptions_renewals LIMIT 10;

-- Iniciamos la query requerida: --
/*
Create a query that extracts the ARR (in EUR) by user_id at a specific date (e.g., 2022-12-31).
Make the date easy to change by putting at the top of the query the following command :
“SET @at_date = ”2022-12-31 23:59:59“.
Be sure to use the right exchange_rate (date related).
*/
-- Fijamos horquilla de fechas para calcular el ARR (recordemos que es un calculo anual o por meses de un año) --
SET @at_date = '2022-12-31 23:59:59';
SET @year_start= '2022-01-01 00:00:00';

-- Calculamos el ARR por usuario (en EUR) --
SELECT 
	s.user_id, 
    SUM(
    -- usamos COALESCE para evitar nulos (deberian estan limpios igualmente)--
        COALESCE(s.net_eur, 0)  -- net EUR subscripciones 
        + COALESCE(s.net_usd * s.exchange_rate, 0)  -- Convertimos USD a EUR para las suscripciones
        + COALESCE(r.net_eur, 0)  -- Valor en EUR de las renovaciones
        + COALESCE(r.net_usd * r.exchange_rate, 0)  -- Convertimos a EUR las renovaciones en USD
    ) AS arr_eur  -- ARR total en EUR sumado todo
FROM 
    subscriptions s
LEFT JOIN 
    subscriptions_renewals r ON s.id = r.renewed_id  -- Conectamos las renovaciones con las suscripciones (dos tablas distintas)
WHERE 
    (s.start_at >= @year_start AND s.start_at <= @at_date)  -- Aplicamos horquilla de fechas
    OR (r.start_at >= @year_start AND r.start_at <= @at_date) 
GROUP BY 
    s.user_id;  -- Agrupamos por usuario
    
    
-- ALEJANDRO SANCHEZ SILVESTRE



