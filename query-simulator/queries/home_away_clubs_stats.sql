-- Запрос 5: Сравнение домашней и выездной статистики клубов по типам покрытия
SELECT 
    c.name AS club,
    s.surface_type,
    SUM(CASE WHEN m.club1_id = c.id THEN 1 ELSE 0 END) AS home_games,
    SUM(CASE WHEN m.club2_id = c.id THEN 1 ELSE 0 END) AS away_games,
    AVG(CASE WHEN m.club1_id = c.id THEN cms1.possession ELSE 0 END) AS avg_home_possession,
    AVG(CASE WHEN m.club2_id = c.id THEN cms2.possession ELSE 0 END) AS avg_away_possession,
    COUNT(DISTINCT CASE WHEN m.club1_id = c.id THEN g.goal_id END) AS home_goals,
    COUNT(DISTINCT CASE WHEN m.club2_id = c.id THEN g.goal_id END) AS away_goals
FROM clubs c
JOIN matches m ON c.id IN (m.club1_id, m.club2_id)
JOIN stadiums s ON c.stadium_id = s.id
LEFT JOIN club_match_stats cms1 ON m.id = cms1.match_id AND c.id = cms1.club_id
LEFT JOIN club_match_stats cms2 ON m.id = cms2.match_id AND c.id = cms2.club_id
LEFT JOIN goals g ON m.id = g.match_id AND g.club_id = c.id
WHERE s.surface_type IN ('Hybrid Grass', 'Artificial Turf')
GROUP BY c.id, s.surface_type
ORDER BY c.name;