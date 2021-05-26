# coding: utf-8
from functools import partial
import multiprocessing

import numpy as np
from sqlalchemy import select, insert, update, func, create_engine


def split_dataframe(df, chunksize):
    if chunksize is not None and chunksize > 0:
        return [
            group[1] for group in df.groupby(np.arange(len(df)) // chunksize)
        ]
    else:
        return [df]


def selectable_from_dataframe(dataframe):
    """ Returns a SQLAlchemy selectable built from a pandas dataframe.

    Each dataframe column maps to a selectable column with same label.
    The column SQLAlchemy type can be specified for each column as a
    keyworkd argument.

    .. warning::
        This feature is for PostgreSQL only.

    """
    return select([
        func.unnest(dataframe[name].tolist()).label(name)
        for name in dataframe.columns.values
    ])


def insert_from_dataframe(table, dataframe, connection, chunksize=None):
    """
    Insert pandas.DataFrame data into a PostgreSQL Table.

    The DataFrame columns must have the same names as the PostgreSQL columns.
    """
    for chunk in split_dataframe(dataframe, chunksize):
        insert_query = insert(table).from_select(
            [
                table.c[name]
                for name in dataframe.columns.values
            ],
            selectable_from_dataframe(chunk))

        connection.execute(insert_query)


def _write_df(
    chunk,
    engine_url,
    table
):
    engine = create_engine(engine_url, pool_size=1, max_overflow=0)
    conn = engine.connect()

    insert_from_dataframe(
        table,
        chunk,
        conn)
    conn.connection.commit()


def parallel_insert_from_dataframe(
    table,
    dataframe,
    connection,
    chunksize=None,
    nb_processes=None
):
    """
    Insert pandas.DataFrame data into a PostgreSQL Table.

    The DataFrame columns must have the same names as the PostgreSQL columns.
    """
    # Check that the given connection is not a transaction
    if connection.in_transaction():
        raise RuntimeError(
            "The connection must not be in transaction as each process has to "
            "commit its query.")

    if nb_processes is None or nb_processes <= 0:
        try:
            nb_processes = multiprocessing.cpu_count()
        except NotImplementedError:
            nb_processes = 1

    # Check that we don't open more connections that the pool can handle
    pool = connection.engine.pool
    max_available_connections = -pool.overflow()
    if max_available_connections <= 0:
        raise RuntimeError("No more connection can be opened to the DataBase")
    if nb_processes >= max_available_connections:
        nb_processes = max_available_connections

    # Create the process pool
    pool = multiprocessing.Pool(processes=nb_processes)

    # Write data
    result = pool.map(partial(
        _write_df,
        engine_url=connection.engine.url,
        table=table
    ), split_dataframe(dataframe, chunksize))

    pool.close()
    pool.join()

    return result


def update_from_dataframe(
    table,
    dataframe,
    connection,
    chunksize=None,
    primary_key='id'
):
    """
    Update pandas.DataFrame data into a PostgreSQL Table.

    The DataFrame columns must have the same names as the PostgreSQL columns.
    """
    for chunk in split_dataframe(dataframe, chunksize):
        sub_query = selectable_from_dataframe(chunk).alias()
        up_query = update(table).where(
            table.c[primary_key] == sub_query.c[primary_key]
        ).values(**sub_query.c)

        connection.execute(up_query)
