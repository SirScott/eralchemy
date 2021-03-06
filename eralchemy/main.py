# -*- coding: utf-8 -*-
from eralchemy.cst import GRAPH_BEGINNING
from eralchemy.sqla import metadata_to_intermediary, declarative_to_intermediary, database_to_intermediary
from pygraphviz.agraph import AGraph
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ArgumentError
try:
    from io import BytesIO as StringIO
except ImportError:
    import StringIO


def intermediary_to_markdown(tables, relationships, output):
    """ Saves the intermediary representation to markdown. """
    er_markup = _intermediary_to_markdown(tables, relationships)
    with open(output, "w") as file_out:
        file_out.write(er_markup)


def intermediary_to_dot(tables, relationships, output):
    """ Save the intermediary representation to dot format. """
    dot_file = _intermediary_to_dot(tables, relationships)
    with open(output, "w") as file_out:
        file_out.write(dot_file)


def intermediary_to_schema(tables, relationships, output):
    """ Transforms and save the intermediary representation to the file chosen. """
    dot_file = _intermediary_to_dot(tables, relationships)
    graph = AGraph()
    graph = graph.from_string(dot_file)
    extension = output.split('.')[-1]
    graph.draw(path=output, prog='dot', format=extension)


def _intermediary_to_markdown(tables, relationships):
    """ Returns the er markup source in a string. """
    rv = StringIO()
    rv.writelines(t.to_er() + '\n' for t in tables)
    rv.writelines(r.to_er() + '\n' for r in relationships)
    return rv.getvalue()


def _intermediary_to_dot(tables, relationships):
    """ Returns the dot source representing the database in a string. """
    rv = StringIO()
    rv.write(GRAPH_BEGINNING)
    rv.write('\n')
    rv.writelines(t.to_dot() + '\n' for t in tables)
    rv.writelines(r.to_dot() + '\n' for r in relationships)
    rv.write('}')
    return rv.getvalue()

# Routes from the class name to the function transforming this class in
# the intermediary representation.
swich_input_class_to_method = {
    'MetaData': metadata_to_intermediary,
    'DeclarativeMeta': declarative_to_intermediary
}

# Routes from the mode to the method to transform the intermediary
#  representation to the desired output.
swich_output_mode_auto = {
    'er': intermediary_to_markdown,
    'graph': intermediary_to_schema,
    'dot': intermediary_to_dot
}

# Routes from the file extension to the method to transform
# the intermediary representation to the desired output.
switch_output_mode = {
    'er': intermediary_to_markdown,
    'dot': intermediary_to_dot,
}


def all_to_intermediary(input):
    """ Dispatch the input to the different function to produce the intermediary syntax.
    All the supported classe names are in `swich_input_class_to_method`.
    """
    input_class_name = input.__class__.__name__
    try:
        this_to_intermediary = swich_input_class_to_method[input_class_name]
        tables, relationships = this_to_intermediary(input)
        return tables, relationships
    except KeyError:
        pass

    try:
        make_url(input)
        return database_to_intermediary(input)
    except ArgumentError:
        pass

    msg = 'Cannot process input {}'.format(input_class_name)
    raise ValueError(msg)


def get_output_mode(output, mode):
    """
    From the output name and the mode returns a the function that will transform the intermediary
    representation to the output.
    """
    if mode != 'auto':
        try:
            return swich_output_mode_auto[mode]
        except KeyError:
            raise ValueError('Mode "{}" is not supported.')

    extension = output.split('.')[-1]
    try:
        return switch_output_mode[extension]
    except KeyError:
        return intermediary_to_schema


def render_er(input, output, mode='auto'):
    """
    Transforms the metadata into a representation.
    :param input: Possible inputs are instances of:
        MetaData: SQLAlchemy Metadata
        DeclarativeMeta: SQLAlchemy declarative Base
    :param output: name of the file to output the
    :param mode: str in list:
        'er': writes to a file the markup to generate an ER style diagram.
        'graph': writes the image of the ER diagram.
        'dot': write to file the diagram in dot format.
        'auto': choose from the filename:
            '*.er': writes to a file the markup to generate an ER style diagram.
            '.dot': returns the graph in the dot syntax.
            else: return a graph to the format graph
    """
    tables, relationships = all_to_intermediary(input)
    intermediary_to_output = get_output_mode(output, mode)
    intermediary_to_output(tables, relationships, output)