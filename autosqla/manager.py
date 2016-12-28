from sqlalchemy import create_engine, inspect
from .mapping import MapperFactory

class AutoSQLA:

    def __init__(self, db_url):
        """Auto SQLAlchemy model mapping manager class
        :param db_uri: Database URI, see http://docs.sqlalchemy.org/en/latest/core/engines.html
        """

        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.engine.connect()
        self.inspector = inspect(self.engine)
        self.mapper = MapperFactory(self)

        self.tables = self.inspector.get_table_names()


    def scan_table(self, table_name):
        """Inspect table from the engine's default connection"""
        return {
            'columns' : self.inspector.get_columns(table_name),
            'indexes' : self.inspector.get_indexes(table_name),
            'foreins' : self.inspector.get_foreign_keys(table_name),
        }


    def print(self, scan = None):
        return self.mapper.make_source()
