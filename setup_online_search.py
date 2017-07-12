import sqlite3

connection = sqlite3.connect("movie_catalogue.db")

cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS old_crews(id INTEGER, first_name TEXT, other_names TEXT, role TEXT, stage_name TEXT, biography TEXT, picture TEXT)''')


