import os
import time
import logging
from prometheus_client import start_http_server, Histogram
import psycopg2
from psycopg2.extensions import parse_dsn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
QUERY_DURATION = Histogram(
    'query_duration_seconds',
    'Time taken to execute SQL query',
    ['query_name'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, float('inf'))
)

class QuerySimulator:
    def __init__(self):
        self.conn = None
        self.queries = {}
        self.load_queries()
        
    def load_queries(self):
        queries_dir = os.path.join(os.path.dirname(__file__), 'queries')
        for filename in os.listdir(queries_dir):
            if filename.endswith('.sql'):
                query_name = os.path.splitext(filename)[0]
                with open(os.path.join(queries_dir, filename), 'r') as f:
                    self.queries[query_name] = f.read()
        logger.info(f"Loaded {len(self.queries)} queries")

    def connect_db(self):
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_ADMIN_USER'),
                password=os.getenv('DB_ADMIN_PASSWORD'),
                host=os.getenv("POSTGRES_HOST", "haproxy"),
                port=os.getenv("POSTGRES_PORT", 5000)
            )
            logger.info("Connected to PostgreSQL database")
        except psycopg2.OperationalError as e:
            logger.error(f"Connection failed: {e}")
            raise

    def execute_query(self, query_name, query_sql):
        try:
            with self.conn.cursor() as cursor:
                start_time = time.time()
                cursor.execute(query_sql)
                duration = time.time() - start_time
                QUERY_DURATION.labels(query_name=query_name).observe(duration)
                logger.info(f"Executed {query_name} in {duration:.4f}s")
                return duration
        except Exception as e:
            logger.error(f"Error executing {query_name}: {e}")
            return None

    def run_queries(self):
        while True:
            try:
                if not self.conn or self.conn.closed:
                    self.connect_db()
                
                for query_name, query_sql in self.queries.items():
                    self.execute_query(query_name, query_sql)
                
                # Interval between query cycles
                time.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("Stopping query simulator")
                break
            except Exception as e:
                logger.error(f"Error in query cycle: {e}")
                time.sleep(10)

if __name__ == '__main__':
    start_http_server(8000)
    logger.info("Prometheus metrics server started on port 8000")
    
    simulator = QuerySimulator()
    simulator.run_queries()
    
    if simulator.conn:
        simulator.conn.close()