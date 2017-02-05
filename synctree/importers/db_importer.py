from .default_importer import DefaultImporter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


class DBImporter(DefaultImporter):
	"""
	A basic DB importer using basic sqlalchemy
	"""
	default_port = None
	dialect = None

	def init(self):
		"""
		Set up the database information
		"""
		self.engine = create_engine(self.engine_string)
		self.session_maker = sessionmaker(
		    bind=self.engine,
		    expire_on_commit=False
		    )

	@contextmanager
	def db_session(self):
	    session = self.session_maker()
	    try:
	        yield session
	        session.commit()
	    except:
	        session.rollback()
	        raise
	    finally:
	        session.close()

	@property
	def engine_string(self):
		user = self.get_setting('db_user')
		_pass = self.get_setting('db_pass')
		host = self.get_setting('db_host', 'localhost')
		port = self.get_setting('db_port', self.default_port)
		database = self.get_setting('db_database')
		return '{}://{}:{}@{}:{}/{}'.format(self.dialect, user, _pass, host, port, database)


class PostgresDBImporter(DBImporter):
	default_port = 5432
	dialect = 'postgresql'
