import os
import psycopg2
from psycopg2 import extras
from faker import Faker
from dotenv import load_dotenv

class DatabaseSeeder:
    def __init__(self):
        load_dotenv()
        self.fake = Faker()
        self.seed_count = int(os.getenv("SEED_COUNT", 100))
        self.conn = psycopg2.connect(**self.get_db_config())
        
    def get_db_config(self):
        return {
            "host": os.getenv("POSTGRES_HOST", "haproxy"),
            "port": os.getenv("POSTGRES_PORT", "5000"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_ADMIN_USER"),
            "password": os.getenv("DB_ADMIN_PASSWORD"),
        }

    def execute_query(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()

    def table_exists_and_empty(self, table):
        result = self.execute_query(f"SELECT COUNT(*) FROM {table}")
        return result[0][0] == 0

    def get_table_columns(self, table_name):
        return self.execute_query("""
            SELECT c.column_name,
                CASE WHEN pg_type.typtype = 'e' THEN pg_type.typname 
                     ELSE c.data_type END AS data_type
            FROM information_schema.columns c
            LEFT JOIN pg_type ON pg_type.typname = c.udt_name
            WHERE c.table_name = %s AND c.table_schema = 'public'
            ORDER BY c.ordinal_position;
        """, (table_name,))
    
    def _get_enum_values(self, enum_name):
        try:
            query = """
                SELECT e.enumlabel 
                FROM pg_enum e 
                JOIN pg_type t ON e.enumtypid = t.oid 
                WHERE t.typname = %s 
                ORDER BY e.enumsortorder;
            """
            result = self.execute_query(query, (enum_name,))
            
            if result:
                return [row[0] for row in result]
            else:
                print(f"Warning: ENUM type '{enum_name}' not found or empty")
                return []
                
        except Exception as e:
            print(f"Error getting ENUM values for '{enum_name}': {e}")
            return []

    def insert_data(self, query, data, table_name):
        try:
            with self.conn.cursor() as cursor:
                extras.execute_values(cursor, query, data, page_size=1000)
                self.conn.commit()
                print(f"Inserted {len(data)} rows into {table_name}")
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting into {table_name}: {str(e)}")

    def generate_row_data(self, table):
        column_handlers = {
            'name': lambda: self.fake.first_name(),
            'surname': lambda: self.fake.last_name(),
            'nationality': self._generate_country,
            'country': self._generate_country,
            'birth_date': lambda: self.fake.date_of_birth(minimum_age=20, maximum_age=50).isoformat(),
            'height_sm': lambda: self.fake.random_int(150, 210),
            'weight_kg': lambda: self.fake.random_int(50, 150),
            'is_right_footed': lambda: self.fake.boolean(),
            'has_fifa_license': lambda: self.fake.boolean(),
            'city': lambda: self.fake.city(),
            'capacity': lambda: self.fake.random_int(5000, 300000),
            'opened_year': lambda: self.fake.random_int(1800, 2025),
            'prize_pool_usd': self._generate_decimal,
            'official_website_url': lambda: self.fake.url(),
            'surface_type': lambda: self.fake.random_element(self._get_enum_values("surface_type"))
        }
        
        row = {}
        for col, dtype in self.get_table_columns(table):
            if col == 'id': continue
            
            if col in column_handlers:
                row[col] = column_handlers[col]()
            elif 'int' in dtype:
                row[col] = self.fake.random_int(1, 1000)
            elif 'date' in dtype:
                row[col] = self.fake.date_this_decade().isoformat()
            elif 'varchar' in dtype or 'text' in dtype:
                row[col] = self.fake.text(50)[:50]
            else:
                row[col] = None
                
        return row

    def _generate_country(self):
        country = self.fake.country()
        return country if len(country) <= 50 else self._generate_country()

    def _generate_decimal(self):
        return round(float(self.fake.pydecimal(left_digits=8, right_digits=2, positive=True)), 2)

    def seed_table(self, table, custom_handler=None, multiplier=1):
        if not self.table_exists_and_empty(table):
            print(f"Skipped seeding {table} table")
            return

        if custom_handler:
            custom_handler()
        else:
            columns = [col for col, _ in self.get_table_columns(table) if col != 'id']
            data = [tuple(self.generate_row_data(table).values()) for _ in range(self.seed_count * multiplier)]
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
            self.insert_data(query, data, table)

    def run_seeding(self):
        independent_tables = ["stadiums", "managers", "tournaments", "referees", "players"]
        for table in independent_tables:
            multiplier = 11 if table == "players" else 1
            self.seed_table(table, multiplier=multiplier)

        seeding_handlers = {
            "clubs": self._seed_clubs,
            "matches": self._seed_matches,
            "club_match_stats": self._seed_club_match_stats,
            "starting_lineups": self._seed_starting_lineups,
            "goals": self._seed_goals,
            "assists": self._seed_assists,
            "clean_sheets": self._seed_clean_sheets,
            "fouls": self._seed_fouls,
            "injuries": self._seed_injuries,
            "substitutions": self._seed_substitutions,
            "league_statistics": self._seed_league_statistics,
            "cup_statistics": self._seed_cup_statistics,
            "personal_awards": self._seed_personal_awards,
            "contracts": self._seed_contracts,
            "transfers": self._seed_transfers
        }
        
        for table, handler in seeding_handlers.items():
            if self.table_exists_and_empty(table):
                handler()

    def _seed_clubs(self):
        stadium_ids = [row[0] for row in self.execute_query("SELECT id FROM stadiums")]
        manager_ids = [row[0] for row in self.execute_query("SELECT id FROM managers")]
        
        data = []
        for _ in range(self.seed_count):
            stadium_id = self.fake.random_element(stadium_ids)
            manager_id = self.fake.random_element(manager_ids)
            stadium_ids.remove(stadium_id)
            manager_ids.remove(manager_id)
            
            data.append([
                self.fake.company(), self.fake.city(), self.fake.random_int(1900, 2025),
                stadium_id, manager_id, self._generate_decimal(), self.fake.url(), False
            ])
        
        self.insert_data("""
            INSERT INTO clubs (name, city, founded_year, stadium_id, manager_id,
                            budget_usd, official_website_url, is_defunct) VALUES %s
        """, data, "clubs")

    def _seed_matches(self):
        tournament_ids = [row[0] for row in self.execute_query("SELECT id FROM tournaments")]
        club_stadiums = [(row[0], row[1]) for row in self.execute_query("SELECT id, stadium_id FROM clubs")]
        referee_ids = [row[0] for row in self.execute_query("SELECT id FROM referees")]
        
        data = []
        for _ in range(self.seed_count):
            tournament_id = self.fake.random_element(tournament_ids)
            club1_id, stadium_id = self.fake.random_element(club_stadiums)
            club2_id = self.fake.random_element([x for x in club_stadiums if x[0] != club1_id])[0]
            
            data.append([
                tournament_id, club1_id, club2_id,
                self.fake.date_between(start_date='-1y', end_date='today'),
                stadium_id, self.fake.random_int(0, 4), self.fake.random_int(0, 4),
                self.fake.random_element(referee_ids), self.fake.random_int(10000, 50000)
            ])
        
        self.insert_data("""
            INSERT INTO matches (tournament_id, club1_id, club2_id, match_date, stadium_id,
                            club1_score, club2_score, referee_id, attendance) VALUES %s
        """, data, "matches")

    def _seed_club_match_stats(self):
        matches = self.execute_query("SELECT id, club1_id, club2_id, club1_score, club2_score FROM matches")
        data = []
        
        for match_id, club1_id, club2_id, score1, score2 in matches:
            possession = self.fake.random_int(30, 70)
            shots1, shots2 = self.fake.random_int(score1, 20), self.fake.random_int(score2, 20)
            
            data.extend([
                [match_id, club1_id, possession, shots1, self.fake.random_int(score1, shots1),
                self.fake.random_int(400, 700), self.fake.random_int(70, 95),
                self.fake.random_int(0, 20), self.fake.random_int(2, 7), self.fake.random_int(3, 15)],
                [match_id, club2_id, 100-possession, shots2, self.fake.random_int(score2, shots2),
                self.fake.random_int(400, 700), self.fake.random_int(70, 95),
                self.fake.random_int(20, 35), self.fake.random_int(2, 7), self.fake.random_int(3, 15)]
            ])
        
        self.insert_data("""
            INSERT INTO club_match_stats (match_id, club_id, possession, shots, shots_on_target,
                                        passes, pass_accuracy, fouls_committed, offsides, corners) VALUES %s
        """, data, "club_match_stats")

    def _seed_starting_lineups(self):
        match_clubs = self.execute_query("SELECT id, club1_id, club2_id FROM matches")
        player_ids = [row[0] for row in self.execute_query("SELECT id FROM players")]
        positions = ["ST", "RW", "LW", "CM", "RM", "LM", "CB", "CB", "LB", "RB", "GK"]
        
        clubs = list(set([club for match in match_clubs for club in [match[1], match[2]]]))
        lineups = {club: self.fake.random_elements(player_ids, 11, True) for club in clubs}
        
        data = []
        for match_id, club1_id, club2_id in match_clubs:
            for i in range(11):
                is_captain = (i == 3)
                data.extend([
                    [match_id, club1_id, lineups[club1_id][i], positions[i], is_captain, "4-3-3"],
                    [match_id, club2_id, lineups[club2_id][i], positions[i], is_captain, "4-3-3"]
                ])
        
        self.insert_data("""
            INSERT INTO starting_lineups (match_id, club_id, player_id, position, is_captain, formation) VALUES %s
        """, data, "starting_lineups")

    def _seed_goals(self):
        matches = self.execute_query("SELECT id, club1_id, club2_id, club1_score, club2_score FROM matches")
        clubs = list(set([club for match in matches for club in [match[1], match[2]]]))
        
        scorers = {}
        for club in clubs:
            result = self.execute_query(f"SELECT player_id FROM starting_lineups WHERE club_id={club} AND position='ST'")
            scorers[club] = result[0][0] if result else None
        
        data = []
        for match_id, club1_id, club2_id, score1, score2 in matches:
            data.extend([[match_id, scorers[club1_id], club1_id, self.fake.random_int(0, 75), 'Open Play'] 
                    for _ in range(int(score1))])
            data.extend([[match_id, scorers[club2_id], club2_id, self.fake.random_int(0, 75), 'Open Play'] 
                    for _ in range(int(score2))])
        
        self.insert_data("""
            INSERT INTO goals (match_id, scorer_id, club_id, goal_mn, goal_type) VALUES %s
        """, data, "goals")

    def _seed_assists(self):
        goals = self.execute_query("SELECT goal_id, match_id, club_id FROM goals")
        clubs = list(set([goal[2] for goal in goals]))
        
        assistants = {}
        for club in clubs:
            result = self.execute_query(f"SELECT player_id FROM starting_lineups WHERE club_id={club} AND position='RW'")
            assistants[club] = result[0][0] if result else None
        
        data = [[match_id, goal_id, assistants[club_id], self.fake.random_int(0, 75)] 
                for goal_id, match_id, club_id in goals]
        
        self.insert_data("""
            INSERT INTO assists (match_id, goal_id, assistant_id, assist_mn) VALUES %s
        """, data, "assists")

    def _seed_clean_sheets(self):
        matches = self.execute_query("SELECT id, club1_id, club2_id, club1_score, club2_score FROM matches")
        clubs = list(set([club for match in matches for club in [match[1], match[2]]]))
        
        keepers = {}
        for club in clubs:
            result = self.execute_query(f"SELECT player_id FROM starting_lineups WHERE club_id={club} AND position IN ('GK', 'CB')")
            keepers[club] = result[0][0] if result else None
        
        data = []
        for match_id, club1_id, club2_id, score1, score2 in matches:
            if int(score2) == 0:  # club1 clean sheet
                data.append([match_id, club1_id, keepers[club1_id]])
            if int(score1) == 0:  # club2 clean sheet  
                data.append([match_id, club2_id, keepers[club2_id]])
        
        self.insert_data("""
            INSERT INTO clean_sheets (match_id, club_id, player_id) VALUES %s
        """, data, "clean_sheets")

    def _seed_fouls(self):
        fouls_data = self.execute_query("SELECT match_id, club_id, fouls_committed FROM club_match_stats")
        foul_types = self._get_enum_values("foul_type")
        
        data = []
        for match_id, club_id, foul_count in fouls_data:
            players = [row[0] for row in self.execute_query(f"SELECT player_id FROM starting_lineups WHERE club_id={club_id}")]
            data.extend([
                [match_id, self.fake.random_element(players), club_id, self.fake.random_int(0, 90), self.fake.random_element(foul_types)]
                for _ in range(int(foul_count))
            ])
        
        self.insert_data("""
            INSERT INTO fouls (match_id, player_id, club_id, foul_mn, foul_type) VALUES %s
        """, data, "fouls")

    def _seed_injuries(self):
        matches = self.execute_query("SELECT match_id, club_id FROM club_match_stats")
        injury_types = self._get_enum_values("injury_type")
        
        data = []
        for match_id, club_id in matches:
            players = [row[0] for row in self.execute_query(f"SELECT player_id FROM starting_lineups WHERE club_id={club_id}")]
            data.append([
                match_id, self.fake.random_element(players), club_id,
                self.fake.random_element(injury_types), self.fake.random_int(0, 90), self.fake.random_int(10, 90)
            ])
        
        self.insert_data("""
            INSERT INTO injuries (match_id, player_id, club_id, injury_type, injury_mn, recovery_days) VALUES %s
        """, data, "injuries")

    def _seed_substitutions(self):
        matches = self.execute_query("SELECT match_id, club_id FROM club_match_stats")
        all_players = [row[0] for row in self.execute_query("SELECT id FROM players")]
        
        data = []
        for match_id, club_id in matches:
            players = [row[0] for row in self.execute_query(f"SELECT player_id FROM starting_lineups WHERE club_id={club_id}")]
            available_subs = list(set(all_players) - set(players))
            
            if players and available_subs:
                data.append([
                    match_id, club_id, self.fake.random_element(players),
                    self.fake.random_element(available_subs), self.fake.random_int(75, 90)
                ])
        
        self.insert_data("""
            INSERT INTO substitutions (match_id, club_id, player_out_id, player_in_id, substitution_mn) VALUES %s
        """, data, "substitutions")
    
    def _seed_league_statistics(self):
        matches = self.execute_query(f"""
            SELECT id, club1_id, club2_id, club1_score, club2_score, tournament_id 
            FROM matches WHERE tournament_id < {int(self.seed_count / 2)}
        """)
        
        stats = {}
        league_counters = {}
        
        for match_id, club1_id, club2_id, score1, score2, tournament_id in matches:
            club1_key = (club1_id, tournament_id)
            club2_key = (club2_id, tournament_id)

            for club_key in [club1_key, club2_key]:
                if club_key not in stats:
                    stats[club_key] = {
                        'matches': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                        'goals_scored': 0, 'goals_conceded': 0, 'points': 0
                    }
                if tournament_id not in league_counters:
                    league_counters[tournament_id] = 1
        
            score1, score2 = int(score1), int(score2)
            
            stats[club1_key]['matches'] += 1
            stats[club1_key]['goals_scored'] += score1
            stats[club1_key]['goals_conceded'] += score2
            
            stats[club2_key]['matches'] += 1
            stats[club2_key]['goals_scored'] += score2
            stats[club2_key]['goals_conceded'] += score1
            
            if score1 > score2:
                stats[club1_key]['wins'] += 1
                stats[club1_key]['points'] += 3
                stats[club2_key]['losses'] += 1
            elif score1 < score2:
                stats[club2_key]['wins'] += 1
                stats[club2_key]['points'] += 3
                stats[club1_key]['losses'] += 1
            else:
                stats[club1_key]['draws'] += 1
                stats[club2_key]['draws'] += 1
                stats[club1_key]['points'] += 1
                stats[club2_key]['points'] += 1
        
        sorted_stats = {}
        for tournament_id in set(key[1] for key in stats.keys()):
            tournament_stats = {key: stat for key, stat in stats.items() if key[1] == tournament_id}
            sorted_tournament = dict(sorted(tournament_stats.items(), 
                                        key=lambda x: x[1]['points'], reverse=True))
            sorted_stats[tournament_id] = sorted_tournament
        
        data = []
        for tournament_id, tournament_stats in sorted_stats.items():
            position = 1
            for (club_id, _), stat in tournament_stats.items():
                data.append([
                    tournament_id, "2024/2025", club_id,
                    stat['matches'], stat['wins'], stat['draws'], stat['losses'],
                    stat['goals_scored'], stat['goals_conceded'], stat['points'], position
                ])
                position += 1
        
        self.insert_data("""
            INSERT INTO league_statistics 
            (league_id, season, club_id, matches_played, wins, draws, losses,
            goals_scored, goals_conceded, points, league_position) VALUES %s
        """, data, "league_statistics")

    def _seed_cup_statistics(self):
        matches = self.execute_query(f"""
            SELECT id, club1_id, club2_id, club1_score, club2_score, tournament_id 
            FROM matches WHERE tournament_id > {int(self.seed_count / 2) + 1}
        """)
        
        stats = {}
        stages = ["1/32", "1/16", "1/8", "1/4", "1/2", "final"]
        
        for match_id, club1_id, club2_id, score1, score2, tournament_id in matches:
            club1_key = (club1_id, tournament_id)
            club2_key = (club2_id, tournament_id)
            
            for club_key in [club1_key, club2_key]:
                if club_key not in stats:
                    stats[club_key] = {
                        'matches': 0, 'goals_scored': 0, 'goals_conceded': 0, 
                        'clean_sheets': 0, 'stage': "1/32", 'is_winner': False
                    }
            
            score1, score2 = int(score1), int(score2)
            
            stats[club1_key]['matches'] += 1
            stats[club1_key]['goals_scored'] += score1
            stats[club1_key]['goals_conceded'] += score2
            if score2 == 0:
                stats[club1_key]['clean_sheets'] += 1
            
            stats[club2_key]['matches'] += 1
            stats[club2_key]['goals_scored'] += score2
            stats[club2_key]['goals_conceded'] += score1
            if score1 == 0:
                stats[club2_key]['clean_sheets'] += 1
            
            if stats[club1_key]['stage'] != "eliminated" and stats[club2_key]['stage'] != "eliminated":
                if score1 > score2:
                    current_stage_index = stages.index(stats[club1_key]['stage'])
                    if current_stage_index < len(stages) - 1:
                        stats[club1_key]['stage'] = stages[current_stage_index + 1]
                    stats[club2_key]['stage'] = "eliminated"
                elif score1 < score2:
                    current_stage_index = stages.index(stats[club2_key]['stage'])
                    if current_stage_index < len(stages) - 1:
                        stats[club2_key]['stage'] = stages[current_stage_index + 1]
                    stats[club1_key]['stage'] = "eliminated"
                else:
                    winner_key = self.fake.random_element([club1_key, club2_key])
                    loser_key = club2_key if winner_key == club1_key else club1_key
                    
                    current_stage_index = stages.index(stats[winner_key]['stage'])
                    if current_stage_index < len(stages) - 1:
                        stats[winner_key]['stage'] = stages[current_stage_index + 1]
                    stats[loser_key]['stage'] = "eliminated"
        
        for club_key, stat in stats.items():
            if stat['stage'] == 'final':
                stat['is_winner'] = self.fake.boolean()
        
        data = []
        for (club_id, tournament_id), stat in stats.items():
            if stat['stage'] != "eliminated": 
                data.append([
                    tournament_id, "2024/2025", club_id,
                    stat['matches'], stat['goals_scored'], stat['goals_conceded'], 
                    stat['clean_sheets'], stat['stage'], stat['is_winner']
                ])
        
        self.insert_data("""
            INSERT INTO cup_statistics 
            (cup_id, season, club_id, matches_played, goals_scored, goals_conceded, 
            clean_sheets, stage_reached, is_winner) VALUES %s
        """, data, "cup_statistics")

    def _seed_personal_awards(self):
        player_ids = [row[0] for row in self.execute_query("SELECT id FROM players")]
        
        data = []
        for _ in range(self.seed_count):
            data.append([
                self.fake.random_element(player_ids),
                self.fake.date_between(start_date='-1y', end_date='today'),
                self.fake.random_element([
                    "Лучший бомбардир сезона",
                    "Лучший ассистент сезона", 
                    "Игрок года",
                    "Лучший молодой игрок",
                    "Лучший вратарь",
                    "Грамота за fair play",
                    "Награда зрительских симпатий"
                ])
            ])
        
        self.insert_data("""
            INSERT INTO personal_awards (player_id, award_date, award_description) VALUES %s
        """, data, "personal_awards")

    def _seed_contracts(self):
        clubs = list(set([row[0] for row in self.execute_query("SELECT id FROM clubs")]))
        player_ids = [row[0] for row in self.execute_query("SELECT id FROM players")]
        status_values = self._get_enum_values("contract_status")
        
        club_assignments = {}
        players_per_club = len(player_ids) // len(clubs)
        
        for i, club_id in enumerate(clubs):
            start_idx = i * players_per_club
            end_idx = start_idx + players_per_club if i < len(clubs) - 1 else len(player_ids)
            club_assignments[club_id] = player_ids[start_idx:end_idx]
        
        data = []
        for club_id, players in club_assignments.items():
            for player_id in players:
                start_date = self.fake.date_between(start_date='-2y', end_date='today')
                data.append([
                    player_id, club_id, start_date,
                    self.fake.date_between(start_date='today', end_date='+3y'),
                    round(float(self.fake.pydecimal(
                        left_digits=self.fake.random_int(6, 8), 
                        right_digits=2, 
                        positive=True
                    )), 2),  # зарплата
                    self.fake.random_element(status_values)
                ])
        
        self.insert_data("""
            INSERT INTO contracts 
            (player_id, club_id, start_date, end_date, salary_usd, status) VALUES %s
        """, data, "contracts")

    def _seed_transfers(self):
        contracts = self.execute_query("SELECT id, player_id, club_id, start_date FROM contracts")
        club_ids = [row[0] for row in self.execute_query("SELECT id FROM clubs")]
        transfer_types = self._get_enum_values("transfer_type")
        
        transfer_contracts = self.fake.random_elements(
            elements=contracts, 
            length=min(self.seed_count, len(contracts)), 
            unique=True
        )
        
        data = []
        for contract in transfer_contracts:
            contract_id, player_id, from_club_id, start_date = contract
            
            to_club_id = self.fake.random_element([cid for cid in club_ids if cid != from_club_id])
            
            data.append([
                player_id, from_club_id, to_club_id, start_date,
                round(float(self.fake.pydecimal(
                        left_digits=self.fake.random_int(8, 10), 
                        right_digits=2, 
                        positive=True
                    )), 2),  # трансферная сумма
                contract_id,
                self.fake.random_element(transfer_types)
            ])
        
        self.insert_data("""
            INSERT INTO transfers 
            (player_id, from_club_id, to_club_id, transfer_date, transfer_fee_usd, 
            contract_id, transfer_type) VALUES %s
        """, data, "transfers")

if __name__ == "__main__":
    seeder = DatabaseSeeder()
    seeder.run_seeding()