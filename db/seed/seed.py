import os
import psycopg2 # type: ignore
from psycopg2 import extras # type: ignore
from faker import Faker # type: ignore
from dotenv import load_dotenv # type: ignore

def get_independent_tables(conn):
    """Получить список таблиц без внешних ключей"""
    with conn.cursor() as cur:
        cur.execute(
        """
            SELECT t.table_name
            FROM information_schema.tables t
            LEFT JOIN (
                SELECT DISTINCT table_name 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY'
            ) fk ON t.table_name = fk.table_name
            WHERE 
                t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                AND fk.table_name IS NULL
                AND t.table_name NOT LIKE 'flyway%' 
        """)
        return [row[0] for row in cur.fetchall()]

def get_dependent_tables(conn):
    """Получить список таблиц c внешними ключами"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT table_name FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY'AND table_schema = 'public'
        """)
        return [row[0] for row in cur.fetchall()]

def get_table_columns(conn, table_name, schema='public'):
    """Возвращает список колонок таблицы с актуальными типами данных (включая enum)"""
    query = """
        SELECT c.column_name,
            CASE 
                WHEN pg_type.typtype = 'e' THEN pg_type.typname 
                ELSE c.data_type 
            END AS data_type
        FROM information_schema.columns c
        LEFT JOIN 
            pg_type ON pg_type.typname = c.udt_name
        WHERE c.table_name = %s AND c.table_schema = %s
        ORDER BY c.ordinal_position;
    """
    with conn.cursor() as cursor:
        cursor.execute(query, (table_name, schema))
        return cursor.fetchall()

def get_enum_names(conn):
    """Возвращает список всех ENUM-типов в схеме public"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT t.typname 
            FROM pg_type t
            JOIN pg_namespace ns ON t.typnamespace = ns.oid
            WHERE t.typtype = 'e'       -- только ENUM-типы
              AND ns.nspname = 'public'  -- только в схеме public
        """)
        return [row[0] for row in cur.fetchall()]

def get_enum_values(conn, enum_type_name):
    """Получить список значений ENUM-типа"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT e.enumlabel 
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = %s
        """, (enum_type_name,))
        return [row[0] for row in cur.fetchall()]

def insert_data(conn, insert_query, insert_data, insert_table):
    with conn.cursor() as cursor:
        try:
            extras.execute_values(
                cursor,
                insert_query,
                insert_data,
                page_size=1000
            )
            conn.commit()
            print(f"Inserted {len(insert_data)} rows into {insert_table}")
        except Exception as e:
            conn.rollback()
            print(f"Error inserting into {insert_table}: {str(e)}")

def generate_data_row(conn, table):
    row = {}
    for col, dtype in get_table_columns(conn, table):
        if col == 'id':
            continue
        if col == "name":
            row[col] = fake.first_name()
        elif col == "surname":
            row[col] = fake.last_name()
        elif col == "nationality" or col == "country":
            country = fake.country()
            while(len(country) > 50): country = fake.country()
            row[col] = country
        elif col == "birth_date":
            row[col] = fake.date_of_birth(minimum_age=20, maximum_age=50).isoformat()
        elif col == "height_sm":
            row[col] = fake.random_int(150, 210)
        elif col == "weight_kg":
            row[col] = fake.random_int(50, 150)
        elif col in ["is_right_footed", "has_fifa_license"]:
            row[col] = fake.boolean()
        elif col == "city":
            row[col] = fake.city()
        elif col == "capacity":
            row[col] = fake.random_int(5000, 300000)
        elif col == "opened_year":
            row[col] = fake.random_int(1800, 2025)
        elif col == "prize_pool_usd":
            row[col] = round(float(fake.pydecimal(
                left_digits=8, 
                right_digits=2, 
                positive=True
            )), 2)
        elif col == "official_website_url":
            row[col] = fake.url()
        elif dtype in get_enum_names(conn):
            enum_values = get_enum_values(conn, dtype)
            row[col] = fake.random_element(enum_values)
        elif 'int' in dtype:
            row[col] = fake.random_int(1, 1000)
        elif 'date' in dtype:
            row[col] = fake.date_this_decade().isoformat()
        elif 'varchar' in dtype or 'text' in dtype:
            row[col] = fake.text(50)[:50]
        else:
            row[col] = None
    
    return row

def seed_independent_tables(conn):
    """Генерация и вставка данных для независимых таблиц"""
    tables = get_independent_tables(conn)
    
    for table in tables:
        columns = [col for col, _ in get_table_columns(conn, table) if col != 'id']
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        if len(cursor.fetchall()) != 0:
            print(f"Skipped seeding {table} table")
            continue
        data = []
        mult = 1
        if (table == "players"): mult = 11
        for _ in range(seed_count * mult):
            row = generate_data_row(conn, table)
            data.append(tuple(row.values()))
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
        insert_data(conn, query, data, table)

def seed_clubs_table(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM stadiums")
    stadium_ids = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT id FROM managers")
    manager_ids = [row[0] for row in cur.fetchall()]

    clubs_data = []
    for _ in range(seed_count):
        stadium_id= fake.random_element(stadium_ids)
        manager_id = fake.random_element(manager_ids)
        stadium_ids.remove(stadium_id)
        manager_ids.remove(manager_id)
        
        clubs_data.append([
            fake.company(), fake.city(), fake.random_int(1900, 2025), stadium_id,
            manager_id,        
            round(float(fake.pydecimal( 
                left_digits=fake.random_int(7,9),          
                right_digits=2, 
                positive=True
            )), 2),
            fake.url(),         
            False                        
        ])
    
    insert_query = """
        INSERT INTO clubs (
            name, city, founded_year, stadium_id, manager_id,
            budget_usd, official_website_url, is_defunct
        ) VALUES %s
    """
    insert_data(conn, insert_query, clubs_data, "clubs")

def seed_matches_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tournaments")
    tournament_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT id, stadium_id FROM clubs")
    club_ids_stadium_ids = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM referees")
    referee_ids = [row[0] for row in cursor.fetchall()]
    data = []
    for _ in range(seed_count):
        tournament_id = fake.random_element(tournament_ids)
        club1_id, stadium_id = fake.random_element(club_ids_stadium_ids)
        club2_id = fake.random_element(club_ids_stadium_ids)[0]
        while (club1_id == club2_id): club2_id = fake.random_element(club_ids_stadium_ids)[0]
        referee_id = fake.random_element(referee_ids)
        data.append([
            tournament_id, club1_id, club2_id,
            fake.date_between(start_date='-1y', end_date='today'),
            stadium_id, fake.random_int(0, 4), fake.random_int(0, 4),
            referee_id, fake.random_int(10000, 50000)
        ])
    insert_query = """
    INSERT INTO matches (
        tournament_id, club1_id, club2_id, match_date, stadium_id, club1_score,
        club2_score, referee_id, attendance
    ) VALUES %s"""
    insert_data(conn, insert_query, data, "matches")

def seed_club_match_stats_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, club1_id, club2_id, club1_score, club2_score FROM matches")
    ids = [(row[0], row[1], row[2], row[3], row[4]) for row in cursor.fetchall()]
    data = []
    for id in ids:
        possession = fake.random_int(30, 70)
        shots1, shots2 = fake.random_int(id[3], 20), fake.random_int(id[4], 20)
        data.append([
            id[0], id[1], possession, shots1, fake.random_int(id[3], shots1),
            fake.random_int(400, 700), fake.random_int(70, 95),
            fake.random_int(0, 20), fake.random_int(2, 7),
            fake.random_int(3, 15)
        ])
        data.append([
            id[0], id[2], 100 - possession, shots2, fake.random_int(id[4], shots2),
            fake.random_int(400, 700), fake.random_int(70, 95),
            fake.random_int(20, 35), fake.random_int(2, 7),
            fake.random_int(3, 15)
        ])
    insert_query = """
    INSERT INTO club_match_stats (
        match_id, club_id, possession, shots, shots_on_target, passes,
        pass_accuracy, fouls_committed, offsides, corners
    ) VALUES %s """
    insert_data(conn, insert_query, data, "club_match_stats")

def seed_starting_lineups_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, club1_id, club2_id FROM matches")
    match_clubs_ids = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM players")
    player_ids = [row[0] for row in cursor.fetchall()]
    enum_values = ["ST", "RW", "LW", "CM", "RM", "LM", "CB", "CB", "LB", "RB", "GK"]
    clubs = []
    for row in match_clubs_ids:
        clubs.append(row[1])
        clubs.append(row[2])
    clubs = list(set(clubs))
    lineups = {}
    for club in clubs:
        players = fake.random_elements(player_ids, 11, True)
        lineups[club] = players
        player_ids = list(set(player_ids) - set(players))
    data = []
    for match in match_clubs_ids:
        for i in range(11):
            flag1, flag2 = False, False
            if (i == 3): flag1, flag2 = True, True
            row1 = [match[0], match[1], lineups[match[1]][i], enum_values[i], flag1, "4-3-3"]
            row2 = [match[0], match[2], lineups[match[2]][i], enum_values[i], flag2, "4-3-3"]
            data += [row1, row2]
    query = """
    INSERT INTO starting_lineups (
        match_id, club_id, player_id, position, is_captain, formation
    ) VALUES %s
    """
    insert_data(conn, query, data, "starting_lineups")

def seed_goals_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, club1_id, club2_id, club1_score, club2_score FROM matches")
    match_clubs_ids = [(row[0], row[1], row[2], row[3], row[4]) for row in cursor.fetchall()]
    clubs = []
    for row in match_clubs_ids:
        clubs.append(row[1])
        clubs.append(row[2])
    clubs = list(set(clubs))
    clubs_scorers = {}
    for club in clubs:
        cursor.execute(f"SELECT player_id FROM starting_lineups WHERE club_id={club} AND position='ST'")
        scorer = int([row[0] for row in cursor.fetchall()][0])
        clubs_scorers[club] = scorer
    goals_data = []
    for line in match_clubs_ids:
        for _ in range(int(line[3])):
            goals_data.append([
                line[0], clubs_scorers[line[1]], line[1], fake.random_int(0, 75), 'Open Play'
            ])
        for _ in range(int(line[4])):
            goals_data.append([
                line[0], clubs_scorers[line[2]], line[2], fake.random_int(0, 75), 'Open Play'
            ])
    query = """
    INSERT INTO goals (
        match_id, scorer_id, club_id, goal_mn, goal_type
    ) VALUES %s
    """
    insert_data(conn, query, goals_data, "goals")

def seed_assists_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT goal_id, match_id, scorer_id, club_id, goal_mn FROM goals")
    goals = [(row[0], row[1], row[2], row[3], row[4]) for row in cursor.fetchall()]
    clubs = list(set([row[3] for row in goals]))
    clubs_assistants = {}
    for club in clubs:
        cursor.execute(f"SELECT player_id FROM starting_lineups WHERE club_id={club} AND position='RW'")
        assistant = int([row[0] for row in cursor.fetchall()][0])
        clubs_assistants[club] = assistant
    data = []
    for line in goals:
        data.append([
            line[1], line[0], clubs_assistants[line[3]], line[4]
        ])
    query = """
    INSERT INTO assists (
        match_id, goal_id, assistant_id, assist_mn
    ) VALUES %s
    """
    insert_data(conn, query, data, "assists")

def seed_clean_sheets_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, club1_id, club2_id, club1_score, club2_score FROM matches")
    matches = [(row[0], row[1], row[2], row[3], row[4]) for row in cursor.fetchall()]
    clubs = []
    for row in matches:
        clubs.append(row[1])
        clubs.append(row[2])
    clubs = list(set(clubs))
    clubs_keepers = {}
    for club in clubs:
        cursor.execute(f"SELECT player_id FROM starting_lineups WHERE club_id={club} AND (position='GK' OR position='CB')")
        keeper = int([row[0] for row in cursor.fetchall()][0])
        clubs_keepers[club] = keeper
    data = []
    for match in matches:
        if (int(match[3]) == 0):
            data.append([
                match[0], match[1], clubs_keepers[match[1]]
            ])
        if (int(match[3]) == 0):
            data.append([
                match[0], match[1], clubs_keepers[match[1]]
            ])
    query = """
    INSERT INTO clean_sheets (
        match_id, club_id, player_id
    ) VALUES %s
    """
    insert_data(conn, query, data, "clean_sheets")

def seed_fouls_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, club_id, fouls_committed FROM club_match_stats")
    matches = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
    foul_types = get_enum_values(conn, "foul_type")
    data = []
    for match in matches:
        cursor.execute(f"SELECT DISTINCT player_id FROM starting_lineups WHERE club_id={match[1]}")
        players = [row[0] for row in cursor.fetchall()]
        for _ in range(int(match[2])):
            data.append([
                match[0], fake.random_element(players), match[1], fake.random_int(0, 90), fake.random_element(foul_types)
            ])
    query = """
    INSERT INTO fouls (
        match_id, player_id, club_id, foul_mn, foul_type
    ) VALUES %s
    """
    insert_data(conn, query, data, "fouls")

def seed_injuries_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, club_id, fouls_committed FROM club_match_stats")
    matches = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
    injury_values = get_enum_values(conn, "injury_type")
    clubs_players = {}
    data = []
    for match in matches:
        cursor.execute(f"SELECT DISTINCT player_id FROM starting_lineups WHERE club_id={match[1]}")
        players = [row[0] for row in cursor.fetchall()]
        data.append([
            match[0], fake.random_element(players), match[1], fake.random_element(injury_values),
            fake.random_int(0, 90), fake.random_int(10, 90)
        ])
    query = """
    INSERT INTO injuries (
        match_id, player_id, club_id, injury_type, injury_mn, recovery_days
    ) VALUES %s
    """
    insert_data(conn, query, data, "injuries")

def seed_substitutions_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, club_id FROM club_match_stats")
    matches = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM players")
    sub_players = [row[0] for row in cursor.fetchall()]
    data = []
    for match in matches:
        cursor.execute(f"SELECT DISTINCT player_id FROM starting_lineups WHERE club_id={match[1]}")
        players = [row[0] for row in cursor.fetchall()]
        data.append([
            match[0], match[1], fake.random_element(players), fake.random_element(sub_players),
            fake.random_int(75, 90)
        ])
    query = """
    INSERT INTO substitutions (
        match_id, club_id, player_out_id, player_in_id, substitution_mn
    ) VALUES %s
    """
    insert_data(conn, query, data, "substitutions")

def seed_league_statistics_table(conn):
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT id, club1_id, club2_id, club1_score, club2_score, tournament_id 
    FROM matches WHERE tournament_id<{int(seed_count / 2)}
    """)
    matches = [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in cursor.fetchall()]
    clubs = []
    league_position_counters = {}
    for match in matches:
        clubs += [(match[1], match[5]), (match[2], match[5])]
        league_position_counters[match[5]] = 1
    clubs = list(set(clubs))
    stats = {}
    for club in clubs: stats[club] = [0, 0, 0, 0, 0, 0, 0] # count, wins, loses, draws, scored, conceded, points
    for match in matches:
        stats[(match[1], match[5])][0] += 1
        stats[(match[2], match[5])][0] += 1
        club1_score, club2_score = int(match[3]), int(match[4])
        stats[(match[1], match[5])][4] += club1_score
        stats[(match[1], match[5])][5] += club2_score
        stats[(match[2], match[5])][4] += club2_score
        stats[(match[2], match[5])][5] += club1_score        
        if (club1_score > club2_score):
            stats[(match[1], match[5])][1] += 1
            stats[(match[1], match[5])][6] += 3
            stats[(match[2], match[5])][2] += 1
        elif (club1_score < club2_score):
            stats[(match[2], match[5])][1] += 1
            stats[(match[2], match[5])][6] += 3
            stats[(match[1], match[5])][2] += 1
        else:
            stats[(match[2], match[5])][3] += 1
            stats[(match[2], match[5])][6] += 1
            stats[(match[1], match[5])][3] += 1
            stats[(match[1], match[5])][6] += 1
    sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1][6], reverse=True))
    counter = 1
    data = []
    for key, stat in sorted_stats.items():
        data.append([
            key[1], "2024/2025", key[0], stat[0], stat[1], stat[3], stat[2], stat[4], stat[5],
            stat[6], league_position_counters[key[1]] 
        ])
        league_position_counters[key[1]] += 1
    query = """
    INSERT INTO league_statistics (
        league_id, season, club_id, matches_played, wins, draws, losses, goals_scored, goals_conceded, points, league_position
    ) VALUES %s
    """
    insert_data(conn, query, data, "league_statistics")

def seed_cup_statistics_table(conn):
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT id, club1_id, club2_id, club1_score, club2_score, tournament_id 
    FROM matches WHERE tournament_id>{int(seed_count / 2) + 1}
    """)
    matches = [(row[0], row[1], row[2], row[3], row[4], row[5]) for row in cursor.fetchall()]
    clubs = []
    for match in matches:
        clubs += [(match[1], match[5]), (match[2], match[5])]
    clubs = list(set(clubs))
    stages = [ "1/8", "1/16", "1/32"]
    stats = {}
    for club in clubs: stats[club] = [0, 0, 0, 0] # count, scored, conceded, clean_sheets
    for match in matches:
        stats[(match[1], match[5])][0] += 1
        stats[(match[2], match[5])][0] += 1
        club1_score, club2_score = int(match[3]), int(match[4])
        stats[(match[1], match[5])][1] += club1_score
        stats[(match[1], match[5])][2] += club2_score
        stats[(match[2], match[5])][1] += club2_score
        stats[(match[2], match[5])][2] += club1_score
        if (club1_score == 0): stats[(match[1], match[5])][3] += 1
        if (club2_score == 0): stats[(match[2], match[5])][3] += 1
    data = []
    for key, stat in stats.items():
        data.append([
            key[1], "2024/2025", key[0], stat[0], stat[1], stat[2], stat[3],
            fake.random_element(stages), False
        ])
    query = """
    INSERT INTO cup_statistics (
    cup_id, season, club_id, matches_played, goals_scored, goals_conceded, clean_sheets, stage_reached, is_winner
    ) VALUES %s
    """
    insert_data(conn, query, data, "cup_statistics")

def seed_personal_awards(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players")
    players = [row[0] for row in cursor.fetchall()]
    data = []
    for _ in range(seed_count):
        data.append([
            fake.random_element(players), fake.date_between(start_date='-1d', end_date='today'),
            "Грамота игрока в футбол"
        ])
    query = """
    INSERT INTO personal_awards (
        player_id, award_date, award_description
    ) VALUES %s
    """
    insert_data(conn, query, data, "personal_awards")

def seed_contracts_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT match_id, club_id FROM club_match_stats")
    clubs = list(set([row[1] for row in cursor.fetchall()]))
    cursor.execute("SELECT id FROM players")
    status = get_enum_values(conn, "contract_status")
    data = []
    for club in clubs:
        cursor.execute(f"SELECT DISTINCT player_id FROM starting_lineups WHERE club_id={club}")
        players = [row[0] for row in cursor.fetchall()]
        for player in players:
            data.append([
                player, club, fake.date_between(start_date='-1y', end_date='today'),
                fake.date_between(start_date='today', end_date='+2y'), 
                round(float(fake.pydecimal(
                    left_digits=fake.random_int(6, 8), 
                    right_digits=2, 
                    positive=True
                )), 2),
                fake.random_element(status)
            ])
    query = """
    INSERT INTO contracts (
        player_id, club_id, start_date, end_date, salary_usd, status
    ) VALUES %s
    """
    insert_data(conn, query, data, "contracts")

def seed_transfers_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, player_id, club_id, start_date FROM contracts")
    contracts = [(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM clubs")
    clubs = [row[0] for row in cursor.fetchall()]
    transfer_types = get_enum_values(conn, "transfer_type")
    data = []
    contracts = fake.random_elements(elements=contracts, length=seed_count, unique=True)
    for contract in contracts:
        club = fake.random_element(clubs)
        while (club == contracts[2]): club = fake.random_element(clubs)
        data.append([
            contract[1], club, contract[2], contract[3], 
            round(float(fake.pydecimal(
                    left_digits=fake.random_int(8, 10), 
                    right_digits=2, 
                    positive=True
            )), 2),
            contract[0], fake.random_element(transfer_types)
        ])
    query = """
    INSERT INTO transfers (
        player_id, from_club_id, to_club_id, transfer_date, transfer_fee_usd, contract_id, transfer_type
    ) VALUES %s
    """
    insert_data(conn, query, data, "transfers")


load_dotenv()
fake = Faker()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "haproxy"),
    "port": os.getenv("POSTGRES_PORT", "5000"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_ADMIN_USER"),
    "password": os.getenv("DB_ADMIN_PASSWORD"),
}

seed_count = int(os.getenv("SEED_COUNT", 100))


conn = psycopg2.connect(**DB_CONFIG)

seed_independent_tables(conn)

launcher = {
    "clubs" : seed_clubs_table,
    "matches" : seed_matches_table,
    "club_match_stats": seed_club_match_stats_table,
    "starting_lineups": seed_starting_lineups_table,
    "goals": seed_goals_table,
    "assists":  seed_assists_table,
    "clean_sheets": seed_clean_sheets_table,
    "fouls": seed_fouls_table,
    "injuries": seed_injuries_table,
    "substitutions": seed_substitutions_table,
    "league_statistics": seed_league_statistics_table,
    "cup_statistics": seed_cup_statistics_table,
    "personal_awards": seed_personal_awards,
    "contracts": seed_contracts_table,
    "transfers": seed_transfers_table
}

dependent_tables = [
    "clubs",
    "matches",
    "club_match_stats",
    "starting_lineups",
    "goals",
    "assists",
    "clean_sheets",
    "fouls",
    "injuries",
    "substitutions",
    "league_statistics",
    "cup_statistics",
    "personal_awards",
    "contracts",
    "transfers"
]


if get_dependent_tables(conn) != []:
    for table in dependent_tables:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        if (len([row for row in cursor.fetchall()]) == 0):
            launcher[table](conn)
        else:
            print(f"Skipped seeding {table} table")