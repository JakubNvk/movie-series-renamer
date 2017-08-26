import os
import re
import sqlite3

folder = '../P&R'
db_name = '../im.db'

conn = sqlite3.connect(db_name)
c = conn.cursor()

for dirname, dirnames, filenames in os.walk(folder):
    counter = 0
    not_renamed = []
    for fn in filenames:
        suffix = fn[-3:]
        m = re.search(r'[sS](?P<season>[0-9]+)[eE](?P<episode>[0-9]+)', fn)

        if m is None:
            m = re.search(r'(?P<season>[0-9]+)[xX](?P<episode>[0-9]+)', fn)
            if m is None:
                counter += 1
                not_renamed.append(fn)

        if m is not None:
            s_e_dict = m.groupdict()

        q = c.execute("""
            SELECT *
            FROM tv_series
            WHERE season=:season AND episode=:episode""", s_e_dict)
        query = q.fetchone()

        if query is not None:
            new_name = '{}/{} - {}x{} - {}.{}'.format(folder, *query, suffix)
            fn = '{}/{}'.format(folder, fn)
            os.rename(fn, new_name)

    print('%d files not renamed. Check the folder.' % counter)
    print('Files not renamed:')
    for fn in not_renamed:
        print(fn)