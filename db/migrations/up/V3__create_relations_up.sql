-- V3__create_related_tables_up.sql

-- Clubs
CREATE TABLE IF NOT EXISTS clubs (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    founded_year INTEGER NOT NULL CHECK (founded_year > 1800),
    stadium_id BIGINT NOT NULL REFERENCES stadiums(id),
    manager_id BIGINT REFERENCES managers(id),
    budget_usd DECIMAL(15,2) CHECK (budget_usd >= 0),
    official_website_url VARCHAR(255),
    is_defunct BOOLEAN NOT NULL DEFAULT false
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id BIGSERIAL PRIMARY KEY,
    tournament_id BIGINT NOT NULL REFERENCES tournaments(id),
    club1_id BIGINT NOT NULL REFERENCES clubs(id),
    club2_id BIGINT NOT NULL REFERENCES clubs(id),
    match_date DATE NOT NULL,
    stadium_id BIGINT NOT NULL REFERENCES stadiums(id),
    club1_score SMALLINT NOT NULL,
    club2_score SMALLINT NOT NULL,
    referee_id BIGINT NOT NULL REFERENCES referees(id),
    attendance INTEGER NOT NULL
);

-- Club match stats
CREATE TABLE IF NOT EXISTS club_match_stats (
    match_id BIGINT NOT NULL REFERENCES matches(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    possession DECIMAL(5,2) NOT NULL,
    shots SMALLINT NOT NULL,
    shots_on_target SMALLINT NOT NULL,
    passes INTEGER NOT NULL,
    pass_accuracy DECIMAL(5,2) NOT NULL,
    fouls_committed SMALLINT NOT NULL,
    offsides SMALLINT NOT NULL,
    corners SMALLINT NOT NULL,
    PRIMARY KEY (match_id, club_id)
);

-- Goals table
CREATE TABLE IF NOT EXISTS goals (
    goal_id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    scorer_id BIGINT NOT NULL REFERENCES players(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    goal_mn SMALLINT NOT NULL CHECK (goal_mn BETWEEN 0 AND 120),
    goal_type goal_type NOT NULL
);

-- Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES players(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL CHECK (end_date > start_date),
    salary_usd DECIMAL(10,2) NOT NULL CHECK (salary_usd >= 0),
    status contract_status NOT NULL
);

-- Transfers table
CREATE TABLE IF NOT EXISTS transfers (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES players(id),
    from_club_id BIGINT NOT NULL REFERENCES clubs(id),
    to_club_id BIGINT NOT NULL REFERENCES clubs(id),
    transfer_date DATE NOT NULL,
    transfer_fee_usd DECIMAL(15,2),
    contract_id BIGINT NOT NULL REFERENCES contracts(id),
    transfer_type transfer_type NOT NULL
);

-- Starting lineups
CREATE TABLE IF NOT EXISTS starting_lineups (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    player_id BIGINT NOT NULL REFERENCES players(id),
    position player_position NOT NULL,
    is_captain BOOLEAN NOT NULL DEFAULT false,
    formation VARCHAR(20) NOT NULL
);

-- Personal awards
CREATE TABLE IF NOT EXISTS personal_awards (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES players(id),
    season VARCHAR(20),
    award_date DATE NOT NULL,
    award_description TEXT NOT NULL
);

-- League statistics
CREATE TABLE IF NOT EXISTS league_statistics (
    id BIGSERIAL PRIMARY KEY,
    league_id BIGINT NOT NULL REFERENCES tournaments(id),
    season VARCHAR(20) NOT NULL,
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    matches_played INTEGER NOT NULL CHECK (matches_played >= 0),
    wins INTEGER NOT NULL CHECK (wins >= 0),
    draws INTEGER NOT NULL CHECK (draws >= 0),
    losses INTEGER NOT NULL CHECK (losses >= 0),
    goals_scored INTEGER NOT NULL CHECK (goals_scored >= 0),
    goals_conceded INTEGER NOT NULL CHECK (goals_conceded >= 0),
    points INTEGER NOT NULL CHECK (points >= 0),
    league_position INTEGER NOT NULL CHECK (league_position > 0)
);

-- Cup statistics
CREATE TABLE IF NOT EXISTS cup_statistics (
    id BIGSERIAL PRIMARY KEY,
    cup_id BIGINT NOT NULL REFERENCES tournaments(id),
    season VARCHAR(20) NOT NULL,
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    matches_played INTEGER NOT NULL CHECK (matches_played >= 0),
    goals_scored INTEGER NOT NULL CHECK (goals_scored >= 0),
    goals_conceded INTEGER NOT NULL CHECK (goals_conceded >= 0),
    clean_sheets INTEGER NOT NULL CHECK (clean_sheets >= 0),
    stage_reached VARCHAR(10) NOT NULL,
    is_winner BOOLEAN NOT NULL DEFAULT false
);

-- Assists
CREATE TABLE IF NOT EXISTS assists (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    goal_id BIGINT NOT NULL REFERENCES goals(goal_id),
    assistant_id BIGINT NOT NULL REFERENCES players(id),
    assist_mn SMALLINT NOT NULL CHECK (assist_mn BETWEEN 0 AND 120)
);

-- Fouls
CREATE TABLE IF NOT EXISTS fouls (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    player_id BIGINT NOT NULL REFERENCES players(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    foul_mn SMALLINT NOT NULL CHECK (foul_mn BETWEEN 0 AND 120),
    foul_type foul_type NOT NULL
);

-- Clean sheets
CREATE TABLE IF NOT EXISTS clean_sheets (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    player_id BIGINT NOT NULL REFERENCES players(id)
);

-- Substitutions
CREATE TABLE IF NOT EXISTS substitutions (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    player_out_id BIGINT NOT NULL REFERENCES players(id),
    player_in_id BIGINT NOT NULL REFERENCES players(id),
    substitution_mn SMALLINT NOT NULL CHECK (substitution_mn BETWEEN 0 AND 120)
);

-- Injuries
CREATE TABLE IF NOT EXISTS injuries (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id),
    player_id BIGINT NOT NULL REFERENCES players(id),
    club_id BIGINT NOT NULL REFERENCES clubs(id),
    injury_type injury_type NOT NULL,
    injury_mn SMALLINT NOT NULL CHECK (injury_mn BETWEEN 0 AND 120),
    recovery_days INTEGER NOT NULL CHECK (recovery_days > 0)
);