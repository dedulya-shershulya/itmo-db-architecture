-- Статистика судей по нарушениям и посещаемости
SELECT 
    r.id AS referee_id,
    r.name || ' ' || r.surname AS referee_name,
    COUNT(DISTINCT m.id) AS total_matches,
    COUNT(f.id) AS total_fouls,
    SUM(
        CASE 
            WHEN f.foul_type IN ('Yellow Card', 'Red Card') THEN 1 
            ELSE 0 
        END
    ) AS disciplinary_actions,
    AVG(m.attendance) AS avg_attendance
FROM referees r
JOIN matches m ON r.id = m.referee_id
LEFT JOIN fouls f ON m.id = f.match_id
GROUP BY r.id, r.name, r.surname
HAVING COUNT(m.id) > 10  
ORDER BY disciplinary_actions DESC;