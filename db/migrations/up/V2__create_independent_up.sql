-- V2__create_independent_tables_up.sql
-- Players table
CREATE TABLE IF NOT EXISTS players (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    birth_date DATE NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    height_sm INTEGER NOT NULL,  
    weight_kg INTEGER NOT NULL,
    is_right_footed BOOLEAN NOT NULL
);

-- Stadiums table
CREATE TABLE IF NOT EXISTS stadiums (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    opened_year INTEGER NOT NULL,
    surface_type surface_type NOT NULL 
);

-- Managers table
CREATE TABLE IF NOT EXISTS managers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    birth_date DATE NOT NULL
);

-- Referees table
CREATE TABLE IF NOT EXISTS referees (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    birth_date DATE NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    has_fifa_license BOOLEAN NOT NULL
);

-- Tournaments table
CREATE TABLE IF NOT EXISTS tournaments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    country VARCHAR(50), 
    prize_pool_usd DECIMAL(15,2),
    official_website_url VARCHAR(255)
);