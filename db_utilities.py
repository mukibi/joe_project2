import sqlite3
from os import remove
from os.path import exists

from shutil import copy

'''Return the entire movie catalogue'''
def read_entire_catalogue(search_params):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()


	#filter by crew
	crew_filtered_ids = {}
	crew_filtered = False

	#title
	select_stmt = "SELECT id,filename,title,year,genre,description,season,episode,cover_picture FROM movies"
	params = ()

	if ( search_params != None ):

		fields_lst = []
		params_lst = []
		search_clause_bts = []

		title = search_params["title"]

		fields_lst.append("filename LIKE ?")
		params_lst.append("%"+title+"%")

		fields_lst.append("title LIKE ?")
		params_lst.append("%"+title+"%")
		
		search_clause = "(" + " OR ".join(fields_lst) + ")"

		search_clause_bts.append(search_clause)

		year = search_params["year"]

		if (len(year) > 0):

			escaped_yr = year[0:4]
			search_clause_bts.append("year LIKE ?")
			params_lst.append("%"+escaped_yr+"%")

		params = (params_lst)

		select_stmt = select_stmt + " WHERE " + " AND ".join(search_clause_bts)

		#print(select_stmt)
		#print(params_lst)

		#crew
		crew = search_params["crew"]
		if (len(crew) > 0):

			crew_filtered = True
			cursor.execute('''SELECT id FROM crews WHERE first_name||" "||other_names LIKE ? OR other_names||" "||first_name LIKE ?''', ("%"+crew+"%", "%"+crew+"%"))

			for row in cursor:
				crew_filtered_ids[row[0]] = 1

	catalogue = {}

	cursor.execute(select_stmt, params)

	for row in cursor:

		if (crew_filtered):

			try:
				mov_id = crew_filtered_ids[row[0]]

			except KeyError:
				continue
		
		catalogue[str(row[0])] = { "filename": row[1] , "title": row[2], "year": row[3], "genre": row[4], "description": row[5], "season": row[6], "episode": row[7], "cover_picture": row[8] }

	connection.close()
	return catalogue

'''Return the entire crew for a movie'''
def read_entire_crew(movie_id):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	crew = {}

	cursor.execute("SELECT first_name,other_names,role,stage_name,biography,picture FROM crews WHERE id=?", (movie_id,))

	cntr = 0

	for row in cursor:

		crew[cntr] = {"first_name": row[0], "other_names": row[1], "role": row[2], "stage_name": row[3], "biography": row[4], "picture": row[5]}

		name = ''

		if ( crew[cntr]["first_name"] != None ):
			name = crew[cntr]["first_name"]

		if ( crew[cntr]["other_names"] != None ):
			name = name + " " + crew[cntr]["other_names"]

		crew[cntr]["name"] = name

		cntr = cntr + 1

	connection.close()
	return crew

'''Reads a value from the configuration table'''
def read_conf(key):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()


	value = None
	cursor.execute("SELECT value FROM configuration WHERE key=?", (key,) )

	for row in cursor:
		value = row[0]

	cursor.close()
	return value

def read_conf_multi(key):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	value = []
	cursor.execute("SELECT value FROM configuration WHERE key=?", (key,) )

	for row in cursor:
		value.append(row[0])

	connection.close()
	return value

def write_conf(key,values):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM configuration WHERE key=?", (key,) )

	for value in values:		
		cursor.execute("INSERT INTO configuration VALUES(?,?)", (key, value))

	connection.commit()
	connection.close()


def update_movie_fields(update_fields, movie_id):

	if (len(update_fields) == 0):
		return

#	print("called update_movie_fields(", update_fields, movie_id, ")")

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	update_stmt_bts    = []
	update_stmt_params = []

	for update_field in update_fields.keys():
	
		if (update_field == "movie_id"):
			continue
		
		update_stmt_bt = "%s=?" % str(update_field)
		update_stmt_bts.append(update_stmt_bt)

		update_stmt_params.append(update_fields[update_field])

	#add movie id param
	update_stmt_params.append(movie_id)
	update_params = tuple(update_stmt_params)

	update_stmt = "UPDATE movies SET %s WHERE id=?" % (", ".join(update_stmt_bts))	

	#print(update_stmt, update_params)

	cursor.execute(update_stmt, update_params)
	connection.commit()
	connection.close()

def update_catalogue(mov_id, key, value):

	#print("update_catalogue(%s,%s,%s)" % (mov_id, key, value))

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("UPDATE movies SET %s=? WHERE id=?" % key, (value, mov_id))
	connection.commit()
	connection.close()

def update_crew(mov_id, crew):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM crews WHERE id=?", (mov_id,))

	for crew_member in crew.keys():

		f_name = crew_member
		o_names = ""

		space = crew_member.find(" ")

		if ( space != -1 ):

			f_name  = crew_member[0:space]
			o_names = crew_member[space+1:]

		cursor.execute("INSERT INTO crews VALUES(?,?,?,?,NULL,NULL,NULL)", (mov_id, f_name, o_names, crew[crew_member]))	

	connection.commit()
	connection.close()

def update_cast(mov_id, crew):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM crews WHERE id=? AND role='cast'", (mov_id,))

	for crew_member in crew.keys():

		f_name = crew_member
		o_names = ""

		space = crew_member.find(" ")

		if ( space != -1 ):

			f_name  = crew_member[0:space]
			o_names = crew_member[space+1:]

		cursor.execute("INSERT INTO crews VALUES(?,?,?,'cast',?,?,?)", (mov_id, f_name, o_names, crew[crew_member]["stage_name"], crew[crew_member]["biography"], crew[crew_member]["picture"]))	

	connection.commit()
	connection.close()


	
def delete_movie(movie_id):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("SELECT cover_picture FROM movies WHERE id=?", (movie_id,) )

	for row in cursor:
		if (row[0] != None):
			remove(row[0])

	cursor.execute("DELETE FROM movies WHERE id=?", (movie_id,))
	
	#delete pictures
	cursor.execute("SELECT picture FROM crews WHERE id=?", (movie_id,) )

	for row in cursor:
		if (row[0] != None):
			remove(row[0])

	cursor.execute("DELETE FROM crews WHERE id=?", (movie_id,))
	
	connection.commit()
	connection.close()

def backup_crew(movie_id):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	#DELETE previous saved backup
	cursor.execute("DELETE FROM old_crews")

	#INSERT into old_crews
	cursor.execute("INSERT INTO old_crews SELECT * FROM crews WHERE id=?", (movie_id,))

	#backup pictures
	cursor.execute("SELECT picture FROM crews WHERE id=?", (movie_id,) )

	for row in cursor:
		if (row[0] != None):
			pic = row[0]
			#print("backup checking", pic)
			if ( exists(pic) ):
				#print("backing up", pic)
				copy(pic, pic + "_dup")	

	connection.commit()
	connection.close()

def restore_movie(movie_id):

	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	#restore cover picture
	cursor.execute("SELECT cover_picture FROM movies WHERE id=?", (movie_id,) )

	for row in cursor:
		if (row[0] != None):

			pic = row[0]
			if ( exists(pic + "_dup") ):
				copy(pic + "_dup", pic)
	

	#restore crew pictures
	cursor.execute("SELECT picture FROM crews WHERE id=?", (movie_id,) )

	for row in cursor:
		if (row[0] != None):
			#print("checking", row[0])
			pic = row[0]
			if ( exists(pic + "_dup") ):
				#print("restoring", pic)
				copy(pic + "_dup", pic)

	#restore db
	cursor.execute("DELETE FROM crews WHERE id=?", (movie_id,) )
	cursor.execute("INSERT INTO crews SELECT * FROM old_crews WHERE id=?", (movie_id,))
	
	connection.commit()
	connection.close()

