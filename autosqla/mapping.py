from string import Template


def MapperFactory(manager):
    # print(manager.engine)
    return DefaultMapper(manager)


class DefaultMapper(object):

    table_template = Template(
"""
class $clsname(Base):
    __tablename__ = "$table_name"

    $columns
""")
    column_template = Template("$name = Column($options)")


    def __init__(self, manager):
        self.manager = manager
        self.imports = set()


    def make_source(self):
        for table_name in self.manager.tables:
            print(self.make_table(table_name))


    def make_class_name(self, table_name):
        """Convert string to CamelCase, example:
            user_transaction => UserTransaction"""

        return ''.join(map(str.capitalize, table_name.split('_')))


    def make_table(self, table_name):
        d = {
            'clsname': self.make_class_name(table_name),
            'table_name': table_name,
        }

        scan = self.manager.scan_table(table_name)

        columns = [self.make_column(column) for column in scan['columns']]
        
        d['columns'] = '\n    '.join(columns)

        return self.table_template.substitute(d)

    def make_column(self, column):
        d = {
            'name': column['name'],
        }
        options = [
            repr(column['type']),
        ]
        d['options'] = ', '.join(options)

        return self.column_template.substitute(d)
