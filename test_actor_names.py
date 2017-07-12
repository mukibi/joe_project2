import sqlite3

connection = sqlite3.connect("movie_catalogue.db")
cursor = connection.cursor()

min_id = 0
max_id = 0

cursor.execute('''SELECT min(id),max(id) FROM movies''')

for row in cursor:
	min_id = row[0]
	max_id = row[1]

movie_id = -1

while (True):

	movie = input("Enter the movie you want to edit (between %d-%d):" % (min_id, max_id,) )

	try:
		movie_id = int(movie)
	except ValueError:
		pass

	if (movie_id == -1):
		print("Invalid input '%s'" % (movie,))
	else:
		break

f_name = None
o_names = None
cursor.execute('''SELECT first_name,other_names FROM crews WHERE id=? LIMIT 1''', (movie_id,))
for row in cursor:
	print("Updating actor %s %s..." % (row[0], row[1],))
	f_name  = row[0]
	o_names = row[1]

new_name =input("Enter the test name for the actor:")

cursor.execute('''UPDATE crews SET first_name=? WHERE id=? AND first_name=? AND other_names=?''', (new_name,movie_id, f_name, o_names))

print("Name updated!")

connection.commit()
connection.close()
