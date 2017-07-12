from os import walk
from os.path import expanduser,join,exists,isdir,basename

import sqlite3
import time

#eyetv_parser.py defines process_eyetv_file()
from eyetv_parser import process_eyetv_file
from online_search import *

paths_to_search = []
eyetv_movies_directory = None
pictures_directory = None

connection = sqlite3.connect("movie_catalogue.db")
cursor = connection.cursor()

#read 'movie_directory' configuration option
#for a list of the directories to search for movie files
#and 'eyetv_movies_directory for the location of
#extracted movie files
param = ('movie_directory','eyetv_movies_directory', 'pictures_directory')

cursor.execute("SELECT key,value FROM configuration WHERE key=? OR key=? OR key=?", param)

for row in cursor:

	#movie_directory
	if (row[0] == "movie_directory"):
		dir_n = row[1]
		if (exists(dir_n) and isdir(dir_n)):
			paths_to_search.append(dir_n)
	#eyetv_movies_directory
	elif ( row[0] == "eyetv_movies_directory" ):
		eyetv_movies_directory = row[1]

	#pictures_directory
	elif ( row[0] == "pictures_directory" ):
		pictures_directory = row[1]

connection.close()

#use the home directory for testing
home_dir = expanduser("~")

if ( len(paths_to_search) == 0 ):
	paths_to_search.append(home_dir)

if (eyetv_movies_directory == None):
	eyetv_movies_directory = home_dir


#run os.walk() to get a list of
#all files in the movie directories
files = []

for path in paths_to_search:

	for (dirpath, dirnames, filenames) in walk(path):
	
		absolute_paths = []

		for filename in filenames:

			absolute_path = join(dirpath, filename)
			absolute_paths.append(absolute_path)

		files.extend(absolute_paths)

num_files = len(files)

#write num files to scan
#connection = sqlite3.connect("movie_catalogue.db")

#cursor = connection.cursor()
#cursor.execute("UPDATE configuration SET value=? WHERE key='num_files'", (str(num_files),) )

#connection.commit()
#connection.close()

#filter out non-movie files
video_file_extensions = {
".3g2":"3GPP2",
".3gp":"3GPP",
".amv":"AMV video format",
".asf":"Advanced Systems Format (ASF)",
".avi":"AVI",
".drc":"Dirac",

".eyetv" : "EyeTV",
".eyetv.zip" : "EyeTV",

".f4v":"Flash Video (FLV)",
".flv":"Flash Video (FLV)",
".f4p":"Flash Video (FLV)",
".f4a":"F4V",
".f4b":"F4V",

#".gif":"GIF",
".gifv":"Video alternative to GIF",
".m4v":"M4V - (file format for videos for iPods and PlayStation Portables developed by Apple)",
".mkv":"Matroska",
".mng":"Multiple-image Network Graphics",

".mov":"QuickTime File Format",
".qt":"QuickTime File Format",

".mp4":"MPEG-4 Part 14 (MP4)",
".m4p":"MPEG-4 Part 14 (MP4)",
".m4v":"MPEG-4 Part 14 (MP4)",

".mpg":"MPEG-1",
".mp2":"MPEG-1",
".mpeg":"MPEG-1",
".mpe":"MPEG-1",
".mpv":"MPEG-1",

".mxf":"Material Exchange Format (MXF)",
".nsv":"Nullsoft Streaming Video (NSV)",

".ogv":"Ogg Video",
".ogg":"Ogg Video",

".rm":"RealMedia (RM)",
".rmvb":"RealMedia Variable Bitrate (RMVB)",
".roq":"ROQ",
".svi":"SVI",

".vob":"Vob",
".webm":"WebM",
".wmv":"Windows Media Video",
".yuv":"Raw video format"

}

cntr = 0

#check files with the expected file extensions
#queing the valid ones
valid_files = {}

#store .eyetv files in a separate list
eyetv_archives = {}

for file_n in files:

	cntr = cntr + 1

	valid = False

	for file_extension in video_file_extensions:

		ext_len = len(file_extension)
		file_n_tail = file_n[-ext_len:]

		if (file_extension == file_n_tail.lower()):
	
			print("Seen %s" % (file_n,))

			valid_files[file_n] = 1

			if ( file_extension == ".eyetv" or file_extension == ".eyetv.zip" ):
				eyetv_archives[file_n] = 1;


			#connection = sqlite3.connect("movie_catalogue.db")
			#cursor = connection.cursor()

			
			#cursor.execute("UPDATE configuration SET value=? WHERE key='processed_files'", (str(cntr),) )
			#cursor.execute("UPDATE configuration SET value=? WHERE key='processing_file'", (file_n,) )
	
			#time_secs = time.mktime(time.gmtime())
			#cursor.execute("UPDATE configuration SET value=? WHERE key='last_access'", (str(time_secs), ))

			#connection.commit()
			#connection.close()

			break

connection = sqlite3.connect("movie_catalogue.db")
cursor = connection.cursor()

#cursor.execute( "UPDATE configuration SET value=? WHERE key='processed_files'", (str(cntr),) )
#connection.commit()


#read all movie filenames currently in the
#movie catalogue
files_in_db = {}
cursor.execute("SELECT filename FROM movies")

for row in cursor:
	file_name = row[0]
	files_in_db[file_name] = 1


#check for new files
new_files = {}

for valid_file in valid_files:

	try:
		val = files_in_db[valid_file]
	except (KeyError):
		new_files[valid_file] = 1

connection.close()

#add new files to DB with null values
for new_file in new_files:

	#connection = sqlite3.connect("movie_catalogue.db")
	#cursor = connection.cursor()

	base_name = basename(new_file)
	( title, year, season, episode ) = parse_filename(base_name)

	#param = (new_file,str(title),str(year), str(season), str(episode))

	#cursor.execute("INSERT INTO movies VALUES(NULL,?,?,?,NULL,NULL,?,?,NULL)", param)
	#connection.commit()

	movie_id = 0

	#cursor.execute("SELECT max(id) FROM movies")

	#for row in cursor:
	#	movie_id = row[0]


	print("Adding %s", new_file)

	#process .eyetv archives
	try:
		is_eyetv = eyetv_archives[new_file]		
		
		print("Adding EyeTV file %s" % new_file)

		attribs = process_eyetv_file(new_file, movie_id, eyetv_movies_directory, pictures_directory)

		update_fields = {}
		update_stmt_bts = {}

		for attrib in attribs.keys():
			
			update_stmt_bt = "%s=?" % str(attrib)
			update_stmt_bts[update_stmt_bt] = 1

			update_fields[attribs[attrib]] = 1

		#add movie id param
		update_fields[movie_id] = 1

		if ( len(update_fields) > 0 ):

			if ( len(update_fields["title"]) > 0 ):
				title = str(update_fields["title"])

			if ( len(update_fields["year"]) > 0 ):
				year = str(update_fields["year"])

			#update_params = tuple(update_fields.keys())
			#update_stmt = "UPDATE movies SET %s WHERE id=?" % (", ".join(update_stmt_bts.keys()))

			#cursor.execute(update_stmt, update_params)
						
	except (KeyError):
		pass

	#connection.commit()
	#connection.close()

	#omdb_search(movie_id, title, year,season, episode)

