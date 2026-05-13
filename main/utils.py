from django.db import connection

def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Useful for Raw SQL queries.
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def dictfetchone(cursor):
    """
    Return one row from a cursor as a dict.
    """
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None
