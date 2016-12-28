import click
from autosqla.manager import AutoSQLA

engines = ['sqlite', 'mysql', 'postgres']

db_url_doc = 'http://docs.sqlalchemy.org/en/latest/core/engines.html'

prompt = """Check this link for more information:
%s

Database connection string, it should be something like:
dialect+driver://username:password@host:port/database

Connection string""" % db_url_doc


@click.group()
def cli():
    pass


@cli.command()
@click.option('db_url', '--dburl',  prompt=prompt, help=db_url_doc)
def generate_model(db_url):
    """Generate SQLAlchemy model file from the database provided"""
    
    manager = AutoSQLA(db_url)
    manager.print()


if __name__ == '__main__':
    cli()