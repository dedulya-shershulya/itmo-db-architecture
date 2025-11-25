-- Запрос 4: Анализ эффективности игроков в разных типах турниров
SELECT p.id,
       p.name || ' ' || p.surname AS player_name,
       t.name AS tournament,
       COUNT(DISTINCT g.goal_id) AS total_goals,
       COUNT(DISTINCT a.id) AS total_assists,
       COUNT(DISTINCT f.id) AS total_fouls,
       AVG(cs.pass_accuracy) AS avg_pass_accuracy
FROM players p
JOIN goals g ON p.id = g.scorer_id
JOIN matches m ON g.match_id = m.id
JOIN tournaments t ON m.tournament_id = t.id
LEFT JOIN assists a ON p.id = a.assistant_id AND a.match_id = m.id
LEFT JOIN fouls f ON p.id = f.player_id AND f.match_id = m.id
JOIN club_match_stats cs ON m.id = cs.match_id AND g.club_id = cs.club_id
GROUP BY p.id, t.id