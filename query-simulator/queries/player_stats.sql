-- Запрос 3: Статистика всех игроков во всех играх 
SELECT p.id
    , p.name
    , p.surname
    , COUNT(g.goal_id) as goals
    , COUNT(a.id) as assists
    , COUNT(f.id) as fouls
    , COUNT(i.id) as injuries
    , COUNT(c.id) as clean_sheets
FROM players p
LEFT JOIN goals g ON p.id = g.scorer_id
LEFT JOIN assists a ON p.id = a.assistant_id
LEFT JOIN fouls f ON p.id = f.player_id
LEFT JOIN injuries i ON p.id = i.player_id
LEFT JOIN clean_sheets c ON p.id = c.player_id
GROUP BY p.id