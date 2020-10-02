import os
import psycopg2
import logging

logger = logging.getLogger(__name__)


class DB:
    def __init__(self):
        self.user = os.environ['POSTGRES_USER']
        self.password = os.environ['POSTGRES_PASSWORD']
        self.db_name = os.environ['DB_NAME']
        self.db_host = os.environ['DB_HOST']

    def create(self):
        db_name = self.db_name
        self.db_name = None
        with self.connection() as connection:
            connection.set_session(autocommit=True)
            cur = connection.cursor()
            cur.execute(f'create database {db_name};')
        self.db_name = db_name

    def drop(self):
        db_name = self.db_name
        self.db_name = None
        with self.connection() as connection:
            connection.set_session(autocommit=True)
            cur = connection.cursor()
            cur.execute(f'DROP DATABASE {db_name};')

    def init(self):
        with self.connection() as connection:
            create_tables = """
            CREATE TABLE platforms (
                id              serial PRIMARY KEY,
                type            varchar(25),
                base_url        varchar(256) unique,
                last_crawl      timestamp
            );
            CREATE TABLE repos (
                id              serial PRIMARY KEY,
                platform_id     integer references platforms(id),
                name            varchar(256),
                owner_name      varchar(256),
                created_at      timestamp,
                last_commit     timestamp,
                description     varchar,
                url             varchar,
                unique(platform_id, owner_name, name)
            )
            """
            cur = connection.cursor()
            cur.execute(create_tables)

    def add_platform(self, instance_type, base_url):
        with self.connection() as connection:
            add_platform = """
            INSERT INTO platforms (
                type,
                base_url
            ) VALUES (%s, %s);
            """
            cur = connection.cursor()
            cur.execute(add_platform, (instance_type, base_url))

    def delete_platform(self, instance_type, base_url):
        with self.connection() as connection:
            del_platform = '''
            DELETE FROM platforms
            WHERE
                type = %s and
                base_url = %s;
            '''
            del_repos = '''
            DELETE FROM repos
            WHERE
                platform_id = %s
            '''
            cur = connection.cursor()
            _id = self.get_platform_id(instance_type, base_url)
            cur.execute(del_repos, (_id,))
            cur.execute(del_platform, (instance_type, base_url))

    def get_platform_id(self, instance_type, base_url):
        with self.connection() as connection:
            select_platform = '''
            SELECT id from platforms
            WHERE
                type = %s and
                base_url = %s;
            '''
            cur = connection.cursor()
            cur.execute(select_platform, (instance_type, base_url))
            return cur.fetchone()

    def get_all_platforms(self):
        with self.connection() as connection:
            cur = connection.cursor()
            cur.execute('select * from platforms')
            return cur.fetchall()

    def add_or_update_results(self, results):
        with self.connection() as connection:
            add_result = '''
            INSERT INTO repos (
                platform_id,
                name,
                owner_name,
                created_at,
                last_commit,
                description,
                url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            '''

            fetch_result = '''
            SELECT id FROM repos
            WHERE
                platform_id = %s and
                name = %s and
                owner_name = %s;
            '''

            update_result = '''
            UPDATE repos
            SET
                name = %s,
                owner_name = %s,
                last_commit = %s,
                description = %s,
                url = %s
            WHERE id = %s;
            '''
            cur = connection.cursor()
            for result in results:
                cur.execute(
                    fetch_result, (result.platform_id,
                                   result.name,
                                   result.owner_name))
                db_result = cur.fetchone()
                if db_result:
                    logger.debug(f'found result {result}, updating...')
                    _id = db_result[0]
                    cur.execute(update_result, (result.name,
                                                result.owner_name,
                                                result.last_commit,
                                                result.description,
                                                result.html_url,
                                                _id))
                else:
                    logger.debug(f'new result, adding {result}')
                    cur.execute(add_result, (result.platform_id,
                                             result.name,
                                             result.owner_name,
                                             result.created_at,
                                             result.last_commit,
                                             result.description,
                                             result.html_url))

    def stats(self):
        with self.connection() as connection:
            cur = connection.cursor()
            cur.execute('select count(*) from repos')
            return cur.fetchall()

    def connection(self):
        return psycopg2.connect(
            host=self.db_host,
            dbname=self.db_name,
            user=self.user,
            password=self.password)
