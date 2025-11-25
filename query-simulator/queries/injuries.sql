-- -- Запрос 2: Анализ травм по позициям
SELECT sl.position, 
       i.injury_type,
       COUNT(*) AS injury_count,
       AVG(i.recovery_days) AS avg_recovery
FROM injuries i
JOIN starting_lineups sl ON i.player_id = sl.player_id 
                         AND i.match_id = sl.match_id
JOIN matches m ON i.match_id = m.id
JOIN tournaments t ON m.tournament_id = t.id
GROUP BY sl.position, i.injury_type;