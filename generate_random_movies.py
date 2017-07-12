from shutil import copy
from os.path import exists

import sqlite3
import random

#backup movie_catalogue.db
if ( exists("movie_catalogue.db") ):
	copy("movie_catalogue.db",  "movie_catalogue.db"+ ".bkp")

connection = sqlite3.connect("movie_catalogue.db")
cursor = connection.cursor()

genres = ["Absurdist/Surreal/Whimsical","Action","Adventure","Comedy","Crime","Drama","Fantasy","Historical","Historical fiction","Horror","Magical realism","Mystery","Paranoid","Philosophical","Political","Romance","Saga","Satire","Science fiction","Slice of Life","Speculative","Thriller","Urban","Western","Animation","Live-action scripted","Live-action unscripted"]
genres_len = len(genres) - 1;


for num in range(1,1000001):

	title = "Test Movie " + str(num)
	genre = genres[random.randint(0, genres_len)]

	yr = 1940 + random.randint(0, 77)

	is_series = random.randint(0,2)

	#one in every 3 is a series
	if (is_series == 2):

		season  = random.randint(1,6) 
		episode = random.randint(1,15) 

		cursor.execute('''INSERT INTO movies VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, NULL)''', ("null_movie_" + str(num),title,yr,genre,title,season,episode))
		#pass

	else:
		cursor.execute('''INSERT INTO movies VALUES(NULL, ?, ?, ?, ?, ?, NULL, NULL, NULL)''', ("null_movie_" + str(num), title,yr,genre,title))
		#pass

connection.commit()
connection.close()


