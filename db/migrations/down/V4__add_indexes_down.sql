-- V4__add_indexes_down.sql
-- flyway: transaction: false
DROP INDEX IF EXISTS idx_transfers_date;
DROP INDEX IF EXISTS idx_transfers_player_club;
DROP INDEX IF EXISTS idx_league_stats_club_points;

DROP INDEX IF EXISTS idx_injuries_match_player;
DROP INDEX IF EXISTS idx_starting_lineups_match_player_position;
DROP INDEX IF EXISTS idx_matches_tournament;

DROP INDEX IF EXISTS idx_goals_scorer;
DROP INDEX IF EXISTS idx_assists_assistant;
DROP INDEX IF EXISTS idx_fouls_player;
DROP INDEX IF EXISTS idx_injuries_player;
DROP INDEX IF EXISTS idx_clean_sheets_player;

DROP INDEX IF EXISTS idx_goals_match_scorer;
DROP INDEX IF EXISTS idx_matches_tournament_date;
DROP INDEX IF EXISTS idx_club_match_stats_match_club;

DROP INDEX IF EXISTS idx_stadiums_surface;
DROP INDEX IF EXISTS idx_matches_clubs;
DROP INDEX IF EXISTS idx_clubs_stadium;

DROP INDEX IF EXISTS idx_matches_referee;
DROP INDEX IF EXISTS idx_fouls_match_type;
DROP INDEX IF EXISTS idx_referees_name;

DROP INDEX IF EXISTS idx_players_name_surname;
DROP INDEX IF EXISTS idx_clubs_name_city;
DROP INDEX IF EXISTS idx_tournaments_name_country;