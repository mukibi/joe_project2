import sqlite3
from os.path import expanduser,join,exists
from os import mkdir
from subprocess import getoutput

import urllib.request
import zipfile
import os
import shutil


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
cursor.execute('''DROP TABLE movies''')
cursor.execute('''CREATE TABLE IF NOT EXISTS movies(id INTEGER PRIMARY KEY, filename TEXT, title TEXT, year TEXT, genre TEXT, description TEXT, season INTEGER,episode INTEGER, cover_picture TEXT)''')

#create 'crews' table
cursor.execute('''DROP TABLE crews''')
cursor.execute('''CREATE TABLE IF NOT EXISTS crews(id INTEGER, first_name TEXT, other_names TEXT, role TEXT, stage_name TEXT, biography TEXT, picture TEXT)''')

#create 'crews' table
cursor.execute('''DROP TABLE old_crews''')
cursor.execute('''CREATE TABLE IF NOT EXISTS old_crews(id INTEGER, first_name TEXT, other_names TEXT, role TEXT, stage_name TEXT, biography TEXT, picture TEXT)''')


#create 'configuration' table
#cursor.execute('''DROP TABLE configuration''')
cursor.execute('''CREATE TABLE IF NOT EXISTS configuration(key TEXT, value TEXT)''')

#configure:
#--eyetv_movies_directory
#--pictures_directory
#--movie_directory

#param = ( "eyetv_movies_directory", eyetv_movies_dir, "pictures_directory", pictures_dir, "movie_directory", home_dir, "player", "xdg-open", "num_files", "0", "processed_files", "0", "processing_file", "", "last_access", "0", "python", "python3", "wemakesites_key", "a1ce18f9-e89c-4177-9c5b-e0670eeb3997" )

#cursor.execute("INSERT INTO configuration VALUES (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?), (?,?)", param)

cursor.execute("INSERT INTO configurations VALUES(?,?)", ("wemakesites_key","a1ce18f9-e89c-4177-9c5b-e0670eeb3997") )

connection.commit()
connection.close()

#install pyqt5
print("Installing PyQt5")
getoutput("pip3 install pyqt5")

#install selenium
print("Installing selenium...")
print(getoutput("pip3 install selenium"))

#install PhantomJS
print("Downloading PhantomJS...")

phantom_js = open("phantom_js.zip", "w+b")

with urllib.request.urlopen("https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-macosx.zip") as f:

	for line in f:
		phantom_js.write(line)

phantom_js.close()

if zipfile.is_zipfile("phantom_js.zip"):

	phantom_zip = zipfile.ZipFile("phantom_js.zip", "r")
		
	members = phantom_zip.namelist();

	for member in members:
		phantom_zip.extract(member)

	phantom_zip.close()

	try: 

		path = os.environ['PATH']
		os_sep = os.pathsep

		path_dirs = path.split(os_sep)

		written = False

		for path_dir in path_dirs:

			if (os.access(path_dir, os.W_OK)):

				shutil.copy("phantomjs-2.1.1-macosx/bin/phantomjs", path_dir)
				written = True
				break

		if (not written):
			print("You do not have write permission to any of the PATH directories. Are you running a privileged account?")
				
	except KeyError:
		print("The PATH environment variable is not set")
	
		



