-- Запрос 1: Анализ эффективности трансферов
SELECT t.transfer_type, 
       c1.name AS from_club,
       c2.name AS to_club,
       AVG(EXTRACT(YEAR FROM AGE(t.transfer_date, p.birth_date))) AS avg_age,
       SUM(ls.points) AS total_points
FROM transfers t
JOIN players p ON t.player_id = p.id
JOIN clubs c1 ON t.from_club_id = c1.id
JOIN clubs c2 ON t.to_club_id = c2.id
JOIN league_statistics ls ON c2.id = ls.club_id 
WHERE t.transfer_date > '2022-01-01'
GROUP BY t.transfer_type, c1.name, c2.name;
