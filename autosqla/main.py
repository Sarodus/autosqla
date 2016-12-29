import re

from sqlalchemy import create_engine, inspect
from collections import defaultdict
from string import Template


class AutoSQLA:

    def __init__(self, db_url):
        """Auto SQLAlchemy model mapping inspector class
        :param db_uri: Database URI, see http://docs.sqlalchemy.org/en/latest/core/engines.html
        """

        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self.engine.connect()
        self.inspector = inspect(self.engine)
        self.mapper = DefaultMapper(self.inspector)

    def make_source(self, scan = None):
        return self.mapper.make_source()


class DefaultMapper(object):

    template_main = Template(
"""
$imports

Base = declarative_base()

$tables""")

    template_table = Template(
"""
class $clsname(Base):
    __tablename__ = "$table_name"

    $columns

    $foreins

    $indexes

""")

    template_column = Template("$name = Column($options)")
    template_forein = Template("$target = relationship(\"$target_cls\")")
    temaplte_index = Template("Index(\"$name\", $options)")
    template_indexes = Template("__table_args__ = ($indexes,)")

    def __init__(self, inspector):
        self.inspector = inspector
        self.column_extra_options = defaultdict(lambda: defaultdict(list))
        self.imports = defaultdict(set)

        self.imports['sqlalchemy.ext.declarative'].add('declarative_base')
        self.imports['sqlalchemy.schema'].add('Column')

    def make_source(self):
        tables = ''
        for table_name in self.inspector.get_table_names():
            tables +=self.make_table(table_name)

        imports = ''
        for module, variables in self.imports.items():
            imports += 'from %s import %s\n' % (module, ', '.join(variables))

        result = self.template_main.substitute(
            imports = imports,
            tables = tables,
        )

        # Clear extra spaces
        result = re.sub(r'^ +$', r'', result, flags=re.M)
        # Clear extra line breaks
        result = re.sub(r'\n\n\n+', r'\n\n\n', result, flags=re.M)
        return result.strip()

    def make_class_name(self, table_name):
        """Convert string to CamelCase, example:
            user_transaction => UserTransaction"""
        return ''.join(map(str.capitalize, table_name.split('_')))

    def make_table(self, table_name):
        d = {
            'clsname': self.make_class_name(table_name),
            'table_name': table_name,
        }

        d['indexes'] = self.make_indexes(table_name, self.inspector.get_indexes(table_name))

        foreins = [self.make_foreins(table_name, forein) for forein in self.inspector.get_foreign_keys(table_name)]
        d['foreins'] = '\n    '.join(foreins)

        columns = [self.make_column(table_name, column) for column in self.inspector.get_columns(table_name)]
        d['columns'] = '\n    '.join(columns)

        # TODO, many_to_many Table() syntax!

        return self.template_table.substitute(d)

    def make_indexes(self, table_name, indexes):
        table_args = []

        for index in indexes:
            if len(index['column_names']) == 1 and index['unique']:
                self.column_extra_options[table_name][index['column_names'][0]].append(
                    'unique=True'
                )
            else:
                options = ['"%s"' % s for s in index['column_names']]
                if index['unique']:
                    options.append('unique=True')

                table_args.append(self.temaplte_index.substitute(name = index['name'], options = ', '.join(options)))

        if table_args:
            self.imports['sqlalchemy.schema'].add('Index')
            return self.template_indexes.substitute(indexes=', '.join(table_args))
        return ''

    def make_foreins(self, table_name, forein):
        if len(forein['referred_columns']) == len(forein['constrained_columns']) == 1:
            d = {
                'target': forein['referred_table'],
                'target_cls': self.make_class_name(forein['referred_table'])
            }

            self.column_extra_options[table_name][forein['constrained_columns'][0]].append(
                'ForeignKey("%s.%s")' % (d['target_cls'], forein['referred_columns'][0])
            )
            self.imports['sqlalchemy.schema'].add('ForeignKey')

            return self.template_forein.substitute(d)
        print('Warning, forein with multiples fields not supported yet!\n%s' % forein)
        return ''

    def make_column(self, table_name, column):
        d = {
            'name': column['name'],
        }

        # TODO, some repr(type) like JSON field, adds extra import dependencies `Column(JSON(astext_type=Text()))`
        options = [
            repr(column['type']),
        ] + self.column_extra_options[table_name][column['name']]

        d['options'] = ', '.join(options)

        # TODO, add nullable, default, onupdate, etc...

        self.imports[column['type'].__module__].add(column['type'].__class__.__name__)

        return self.template_column.substitute(d)
