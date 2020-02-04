""" Import imdb open .tsv data to PostgreSQL database.
Files to import (data_ratings.tsv, data_titles.tsv), get these at https://datasets.imdbws.com/
should be in the same path as import_tsv.py script.
"""
import psycopg2
import time
import io

st = time.time()

connection = psycopg2.connect(
    host='localhost',
    dbname='imdb',
    port='5432',
    user='django',
    password='django'
)
cursor = connection.cursor()

print('Dropping old database tables...')
cursor.execute('DROP TABLE IF EXISTS titles')
cursor.execute('DROP TABLE IF EXISTS ratings')
connection.commit()

print('Creating database tables...')
cursor.execute(
    '''CREATE TABLE ratings
    (
        tconst text PRIMARY KEY,
        average_rating decimal(3, 1),
        num_votes integer
    )'''
)
cursor.execute(
    '''CREATE TABLE titles
    (   
        tconst text PRIMARY KEY,
        title_type text,
        primary_title text,
        original_title text,
        is_adult bool,
        start_year integer,
        end_year integer,
        runtime_mins integer,
        genres text
    )'''
)

print('Importing data_ratings.tsv...')
with open('data_ratings.tsv') as ratings:
    # Omit header
    ratings.readline()
    cursor.copy_from(ratings, 'ratings')

connection.commit()

print('Importing data_titles.tsv...')
with open('data_titles.tsv', encoding='utf-8') as titles:
    # Omit header
    titles.readline()
    cursor.copy_from(titles, 'titles')

cursor.execute('ALTER TABLE titles ALTER COLUMN genres TYPE text[] USING string_to_array(genres, \',\')')
connection.commit()

print('Creating titles table indexes...')
cursor.execute('CREATE INDEX genres_idx ON titles (genres)')
cursor.execute('CREATE INDEX start_year_idx ON titles (start_year)')

connection.close()

print()
print('Done.\n Executed in (sec):', time.time() - st)