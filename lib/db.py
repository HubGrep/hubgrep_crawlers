import os
import psycopg2
import logging
from psycopg2.extras import Json, RealDictCursor

from lib.platforms import platforms

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

    def query(self, q, limit):
        query = """
        SELECT
            platforms.base_url,
            repos.name,
            repos.owner_name,
            repos.description,
            ts_rank(to_tsvector('english', name || ' ' || description), plainto_tsquery(%s)) as rank
        FROM repos
        inner join platforms ON
            platforms.id = repos.platform_id
        WHERE
            plainto_tsquery(%s)
            @@
            to_tsvector('english', name || ' ' || description)
        ORDER BY rank desc
        """
        with self.connection() as connection:
            cur = connection.cursor()
            if limit:
                query += 'LIMIT %s'
                cur.execute(query, (q, q, limit))
            else:
                cur.execute(query, (q, q, ))
            return cur.fetchall()

    def init(self):
        with self.connection() as connection:
            create_tables = """
            CREATE TABLE platforms (
                id              serial PRIMARY KEY,
                type            varchar(25),
                base_url        varchar(256) unique,
                auth_data       json,
                last_crawl      timestamp,
                state           json
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
            create_gin_index = """
            CREATE INDEX
                 name_description_idx
             ON repos
             USING GIN
                 (to_tsvector('english', name || ' ' || description));
            """
            create_repo_index = """
            CREATE INDEX name_owner_name_index ON repos
 (name, owner_name);
            """
            cur = connection.cursor()
            cur.execute(create_tables)
            cur.execute(create_gin_index)

    def platform_add(self, instance_type, base_url, auth_data=None):
        with self.connection() as connection:
            add_platform = """
            INSERT INTO platforms (
                type,
                base_url,
                auth_data
            ) VALUES (%s, %s, %s);
            """
            cur = connection.cursor()
            cur.execute(
                add_platform,
                (instance_type,
                 base_url,
                 Json(auth_data)))

    def platform_delete(self, instance_type, base_url):
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
            platform = self.platform_get(instance_type, base_url)
            cur.execute(del_repos, (platform._id,))
            cur.execute(del_platform, (instance_type, base_url))

    def platform_get(self, instance_type, base_url):
        with self.connection() as connection:
            select_platform = '''
            SELECT
                *
            from
                platforms
            WHERE
                type = %s and
                base_url = %s;
            '''
            cur = connection.cursor(cursor_factory=RealDictCursor)
            Platform = platforms.get(instance_type, False)
            if Platform:
                cur.execute(select_platform, (instance_type, base_url))
                return Platform(**cur.fetchone())
            else:
                return False

    def platform_get_all(self, base_url=None, platform=None):
        with self.connection() as connection:
            cur = connection.cursor(cursor_factory=RealDictCursor)
            print(cur)
            if base_url:
                cur.execute('''
                select *
                from platforms
                where base_url = %s
                ''', (base_url, ))
            elif platform:
                cur.execute('''
                select *
                from platforms
                where type = %s
                ''', (platform, ))
            else:
                cur.execute('select * from platforms')

            platform_objects = []
            for platform_data in cur.fetchall():
                Platform = platforms.get(platform_data['type'], False)
                if Platform:
                    platform_objects.append(Platform(**dict(platform_data)))
                else:
                    logger.error(
                        f'no class for {platform_data["type"]} found!')
            return platform_objects

    def platform_update_state(self, _id, state):
        with self.connection() as connection:
            update_state = """
            UPDATE platforms
            SET
                state = %s
            WHERE
                id = %s
            """
            cur = connection.cursor()
            cur.execute(update_state, (Json(state), _id))

    def results_add_or_update(self, results):
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
                created_at = %s,
                last_commit = %s,
                description = %s,
                url = %s
            WHERE id = %s;
            '''
            cur = connection.cursor()
            logger.debug(f'adding {len(results)} results')
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
                                                result.created_at,
                                                result.last_commit,
                                                result.description,
                                                result.html_url,
                                                _id))
                else:
                    #logger.debug(f'new result, adding {result}')
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
            cur.execute('''
                        select
                            platforms.type,
                            platforms.base_url,
                            count(repos.id) as count
                        from repos
                        inner join platforms ON
                            platforms.id = repos.platform_id
                        group by
                            platforms.id
                        order by
                            count desc
                        ;
                        ''')
            return cur.fetchall()

    def connection(self):
        return psycopg2.connect(
            host=self.db_host,
            dbname=self.db_name,
            user=self.user,
            password=self.password)
