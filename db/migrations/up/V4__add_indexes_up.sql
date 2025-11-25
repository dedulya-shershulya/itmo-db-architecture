-- V4__add_indexes_up.sql
-- flyway: transaction: false

-- Индексы для Запроса 1 (Анализ трансферов)
CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(transfer_date);
CREATE INDEX IF NOT EXISTS idx_transfers_player_club ON transfers(player_id, from_club_id, to_club_id);
CREATE INDEX IF NOT EXISTS idx_league_stats_club_points ON league_statistics(club_id, points);

-- Индексы для Запроса 2 (Анализ травм)
CREATE INDEX IF NOT EXISTS idx_injuries_match_player ON injuries(match_id, player_id);
CREATE INDEX IF NOT EXISTS idx_starting_lineups_match_player_position ON starting_lineups(match_id, player_id, position);
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id);

-- Индексы для Запроса 3 (Статистика игроков)
CREATE INDEX IF NOT EXISTS idx_goals_scorer ON goals(scorer_id);
CREATE INDEX IF NOT EXISTS idx_assists_assistant ON assists(assistant_id);
CREATE INDEX IF NOT EXISTS idx_fouls_player ON fouls(player_id);
CREATE INDEX IF NOT EXISTS idx_injuries_player ON injuries(player_id);
CREATE INDEX IF NOT EXISTS idx_clean_sheets_player ON clean_sheets(player_id);

-- Индексы для Запроса 4 (Эффективность в турнирах)
CREATE INDEX IF NOT EXISTS idx_goals_match_scorer ON goals(match_id, scorer_id);
CREATE INDEX IF NOT EXISTS idx_matches_tournament_date ON matches(tournament_id, match_date);
CREATE INDEX IF NOT EXISTS idx_club_match_stats_match_club ON club_match_stats(match_id, club_id);

-- Индексы для Запроса 5 (Сравнение статистики)
CREATE INDEX IF NOT EXISTS idx_stadiums_surface ON stadiums(surface_type);
CREATE INDEX IF NOT EXISTS idx_matches_clubs ON matches(club1_id, club2_id);
CREATE INDEX IF NOT EXISTS idx_clubs_stadium ON clubs(stadium_id);

-- Индексы для Статистики судей
CREATE INDEX IF NOT EXISTS idx_matches_referee ON matches(referee_id);
CREATE INDEX IF NOT EXISTS idx_fouls_match_type ON fouls(match_id, foul_type);
CREATE INDEX IF NOT EXISTS idx_referees_name ON referees(name, surname);

-- Составные индексы для часто используемых комбинаций
CREATE INDEX IF NOT EXISTS idx_players_name_surname ON players(name, surname);
CREATE INDEX IF NOT EXISTS idx_clubs_name_city ON clubs(name, city);
CREATE INDEX IF NOT EXISTS idx_tournaments_name_country ON tournaments(name, country);
