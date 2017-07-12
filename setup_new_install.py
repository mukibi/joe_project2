import sqlite3
from os.path import expanduser,join,exists
from os import mkdir
from subprocess import getoutput

#create directories
home_dir = expanduser("~")

#eyetv_movies directory
eyetv_movies_dir = join(home_dir, "movie_catalogue_eyetv")
if (not exists(eyetv_movies_dir)):
	mkdir(eyetv_movies_dir)

#pictures directory
pictures_dir = join(home_dir, "movie_catalogue_pictures")
if (not exists(pictures_dir)):
	mkdir(pictures_dir)

#thumbanils directory
thumbnails_dir = join(pictures_dir, "thumbnails")
if (not exists(thumbnails_dir)):
	mkdir(thumbnails_dir)

#full pictures
full_pics_dir = join(pictures_dir, "full")
if (not exists(full_pics_dir)):
	mkdir(full_pics_dir)

connection = sqlite3.connect("movie_catalogue.db")

cursor = connection.cursor()

#create 'movies' table
#cursor.execute('''DROP TABLE movies''')
cursor.execute('''CREATE TABLE IF NOT EXISTS movies(id INTEGER PRIMARY KEY, filename TEXT, title TEXT, year TEXT, genre TEXT, description TEXT, season INTEGER,episode INTEGER, cover_picture TEXT)''')

#create 'crews' table
#cursor.execute('''DROP TABLE crews''')
cursor.execute('''CREATE TABLE IF NOT EXISTS crews(id INTEGER, first_name TEXT, other_names TEXT, role TEXT, stage_name TEXT, biography TEXT, picture TEXT)''')

#create 'configuration' table
#cursor.execute('''DROP TABLE configuration''')
cursor.execute('''CREATE TABLE IF NOT EXISTS configuration(key TEXT, value TEXT)''')

#configure:
#--eyetv_movies_directory
#--pictures_directory
#--movie_directory

param = ( "eyetv_movies_directory", eyetv_movies_dir, "pictures_directory", pictures_dir, "movie_directory", home_dir, "player", "xdg-open", "num_files", "0", "processed_files", "0", "processing_file", "", "last_access", "0", "python", "python3", "wemakesites_key", "a1ce18f9-e89c-4177-9c5b-e0670eeb3997" )

cursor.execute("INSERT INTO configuration VALUES (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?)", param)

#cursor.execute("INSERT INTO configurations VALUES(?,?)", ("wemakesites_key","a1ce18f9-e89c-4177-9c5b-e0670eeb3997") )

connection.commit()
connection.close()

#install pyqt5
getoutput("pip install pyqt5")
