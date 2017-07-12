from os.path import join,isfile,exists
from os import listdir

from db_utilities import *
from online_search import *

import sys
import re
import time

import subprocess
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import sip

import shlex

'''Stores variables that may be needed
across function calls such as the main window'''
class MyWidget:

	table = None
	main_window = None
	runs = 0
	catalogue = {}
	crews = {}
	current_movie = None
	update_list = {}
	description_editor = None
	progress_bar = None
	progress_label = None
	total_files = None
	timer = None
	settings_vars = None
	search_field = None
	year_field = None
	crew_field = None

	display_title_field = None
	display_year_field  = None
	display_season_field  = None
	display_episode_field = None

	display_filename_field = None

	crews_table = None

	download_complete = False
	download_timer = None

	search_results = {}

	grid = None
	crews_table = None

	poster_label = None

	unsaved_changes = False
	searched_online = False

	search_stopped = False

	displaying_crew = False

	ad_remover_progress_bar = None
	ad_remover_progress_label = None

	ad_remover_timer = None

my_widget = MyWidget()

'''Search movie catalogue for a movie'''
def search_catalogue():

	search_vals = {}

	search_val = my_widget.search_field.text()
	search_vals["title"] = search_val

	year_val = my_widget.year_field.text()
	search_vals["year"] = year_val

	crew_val = my_widget.crew_field.text()
	search_vals["crew"] = crew_val
	
	load_catalogue(my_widget.main_window, search_params=search_vals)

'''Open the search and filter dialog'''
def search():

	widget = QWidget()
	widget.setMaximumHeight(200)

	grid = QGridLayout()

	row_index = 0

	search_label = QLabel("Title/Filename")
	grid.addWidget(search_label, row_index, 0)

	search_field = QLineEdit("")

	grid.addWidget(search_field, row_index, 1)
	my_widget.search_field = search_field

	row_index = row_index + 1

	year_label = QLabel("Year")
	grid.addWidget(year_label, row_index, 0)

	year_field = QLineEdit("")

	grid.addWidget(year_field, row_index, 1)
	my_widget.year_field = year_field

	row_index = row_index + 1

	crew_label = QLabel("Crew Name")
	grid.addWidget(crew_label, row_index, 0)

	crew_field = QLineEdit("")
	grid.addWidget(crew_field, row_index, 1)

	my_widget.crew_field = crew_field
	
	row_index = row_index + 1

	search_pixmap = QPixmap("search-icon.png")

	search_icon = QIcon(search_pixmap)

	search_button = QToolButton()
	search_button.setIcon(search_icon)
	search_button.setIconSize(QSize(24, 24))

	search_action = QAction(search_icon, "Search Movie Catalogue", search_button)
	search_button.setDefaultAction(search_action)

	search_button.triggered.connect(search_catalogue)

	grid.addWidget(search_button, row_index, 0, 2, 1)
	widget.setLayout(grid)

	window = my_widget.main_window;
	window.setCentralWidget(widget)

def save_conf():
	
	settings_vars = my_widget.settings_vars

	movie_dirs = []

	for settings_var in settings_vars:
		
		field = settings_vars[settings_var]
		val = field.text()

		#movies_directory
		if (settings_var[0:-1] == "movie_directory"):
			movie_dirs.append(val)

		else:
			write_conf(settings_var, [val])

	write_conf("movie_directory", movie_dirs)

	msg = QMessageBox()
	msg.setIcon(QMessageBox.Information)

	msg.setText("The settings have been successfully saved!")
	msg.setWindowTitle("Settings Saved")
	msg.setStandardButtons(QMessageBox.Ok)
	
	retval = msg.exec_()

			
'''Change configuration options'''
def settings():

	widget = QWidget()

	grid = QGridLayout()

	sorted_variables = ["eyetv_movies_directory", "pictures_directory", "movie_directory", "player", "python"]

	variables = {"eyetv_movies_directory": "Directory to store extracted EyeTV movies", "pictures_directory": "Directory to store pictures", "movie_directory": "Directories to search for movies", "player": "Default movie player", "python": "Python executable"}
 
	row_index = 0;

	settings_vars = {}
	
	for variable in ( sorted_variables ):

		var_label = QLabel(variables[variable])
		rowspan = 1

		if ( variable == "movie_directory" ):
			rowspan = 3

		grid.addWidget(var_label, row_index, 0, rowspan,1)
	
		if ( variable == "movie_directory" ):

			vals = read_conf_multi(variable)
			num_set_vals = len(vals)

			rem = 3 - num_set_vals

			#add the remaining textfields
			for j in range(rem):
				vals.append("")

			cntr = 0	
			for val in vals:

				if (val == None):
					val = ""

				txt_field = QLineEdit(val)
				grid.addWidget(txt_field, row_index, 1)

				cntr = cntr + 1
				row_index = row_index + 1
				settings_vars[variable + str(cntr)] = txt_field

			line = QFrame()
			line.setFrameShape(QFrame.HLine)
			line.setFrameShadow(QFrame.Sunken)

			line.setStyleSheet("border: 2px dotted white")

			grid.addWidget(line, row_index, 0, 1, 2)

			row_index = row_index + 1

		else:

			val = read_conf(variable)

			if (val == None):
				val = ""

			txt_field = QLineEdit(val)

			grid.addWidget(txt_field, row_index, 1)

			row_index = row_index + 1

			line = QFrame()
			line.setFrameShape(QFrame.HLine)
			line.setFrameShadow(QFrame.Sunken)

			line.setStyleSheet("border: 2px dotted white")
			grid.addWidget(line, row_index, 0, 1, 2)

			row_index = row_index + 1
		
			settings_vars[variable] = txt_field

	save = QPushButton("Save")
	save.clicked.connect(save_conf)

	grid.addWidget(save, row_index + 1, 0)
	widget.setLayout(grid)

	window = my_widget.main_window;
	window.setCentralWidget(widget)

	my_widget.settings_vars = settings_vars

'''Launch filesystem scanner'''
def scan():

	widget = QWidget()
	widget.setMaximumHeight(200)

	current_time = time.mktime(time.gmtime())
	last_access = read_conf("last_access")

	if (last_access == None):
		last_access = 0

	#ran more than 10 seconds ago
	#relaunch
	python = read_conf("python")
	if (python == None):
		python = "python"

	if ( (current_time - float(last_access)) > 10 ):
		subprocess.Popen( [python, "filesystem_scan.py"], shell=False,stdin=None,stdout=None,stderr=None,close_fds=True)

	grid = QGridLayout()

	progress_bar_pt = 0	
	progress_bar = QProgressBar()
	progress_bar.setGeometry(30,40,200, 25)

	grid.addWidget(progress_bar, 0,0)

	label = QLabel("")
	grid.addWidget(label, 1, 0)

	widget.setLayout(grid)

	grid.setAlignment(progress_bar, Qt.AlignVCenter)
	#grid.setAlignment(progress_bar, Qt.AlignHCenter)

	grid.setAlignment(label, Qt.AlignTop)
	#grid.setAlignment(label, Qt.AlignHCenter)


	window = my_widget.main_window;
	window.setCentralWidget(widget)

	total_files = int(read_conf("num_files"))

	my_widget.progress_bar = progress_bar
	my_widget.progress_label = label
	my_widget.total_files = total_files

	timer = QTimer()
	timer.setInterval(1000)
	my_widget.timer = timer

	timer.timeout.connect(check_progress)
	timer.start()

def check_progress():

	total_files = my_widget.total_files

	processed_files = int(read_conf("processed_files"))
	percent = 100

	if (total_files > 0):
		percent = int( (int(processed_files) / total_files) * 100 )
	
	my_widget.progress_bar.setValue(percent)
	
	current_file = read_conf("processing_file")
	if (current_file == None):
		current_file = ""

	my_widget.progress_label.setText("Checking " + current_file + "...")

	if ( percent >= 100 ):
		my_widget.timer.stop()

def refresh_display():

	#print("called refresh_display()")

	if (my_widget.searched_online and my_widget.download_complete):

		#print("Refreshing display")

		my_widget.searched_online = False
		my_widget.download_complete = False

		results = my_widget.search_results

		if (len(results) == 0):

			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)

			msg.setText("The search did not return any results.")
			msg.setWindowTitle("No results")
			msg.setStandardButtons(QMessageBox.Ok)
	
			retval = msg.exec_()

			my_widget.download_timer.stop()
			restore_movie(my_widget.current_movie)

			my_widget.download_timer = None

			my_widget.unsaved_changes = False
			#my_widget.searched_online = False

			return
			#alert

		#print(results)

		#cover pic
		movie_poster_file = "blank_movie_poster.png";

		try:
			cover_pic = results["cover_picture"]

			if ( exists(cover_pic) ):
				movie_poster_file = cover_pic

		except KeyError:
			pass

		window_width = my_widget.main_window.width()

		poster_pixmap = QPixmap(movie_poster_file)	
		poster_pixmap = poster_pixmap.scaledToWidth((window_width *0.4))

		my_widget.poster_label.setPixmap(poster_pixmap)

		#my_widget.grid.replaceWidget(my_widget.crews_table, new_crews_table)
		
		#update fields
		for header in results:

			if ( header == "title" ):	
				my_widget.display_title_field.setText(results[header])

			elif ( header == "year" ):
				my_widget.display_year_field.setText(results[header])

			elif ( header == "season" ):
				my_widget.display_season_field.setText(results[header])

			elif ( header == "episode" ):
				my_widget.display_episode_field.setText(results[header])

			elif ( header == "genre" ):
				my_widget.display_genre_field.setText(results[header])

			elif ( header == "description" ):
				my_widget.description_editor.setText(results[header])

		#rebuild casts table
		new_crews = read_entire_crew(my_widget.current_movie)	
		new_crews_table = build_crews_table(new_crews)

		#my_widget.grid.removeWidget(my_widget.crews_table)

		#if ( my_widget.crews_table == None ):
		#my_widget.grid.addWidget(new_crews_table)

		#else:
		#	print("Doing replacewidget")

		my_widget.crews_table.close()
		my_widget.grid.replaceWidget(my_widget.crews_table, new_crews_table)

		crews = read_entire_crew(my_widget.current_movie)

		my_widget.crews = crews

		#print("Replaced crews table\n")

		my_widget.crews_table = new_crews_table

		#print("display_movie()")
		#display_movie(my_widget.main_window, my_widget.current_movie)

		#my_widget.download_complete = True
		my_widget.download_timer.stop()
		my_widget.search_results = {}
		my_widget.download_timer = None

'''Process clicked row'''
def row_clicked(row, col):

	table = my_widget.table
	header = table.item(row, 5) 
	
	movie_id = header.text()

	#print("display_movie()")
	display_movie(my_widget.main_window, movie_id)


'''Display the entries in the catalogue'''
def load_catalogue(main_window,search_params):

	my_widget.crews_table = None

	catalogue = read_entire_catalogue(search_params)


	my_widget.catalogue = catalogue

	num_rows = len(my_widget.catalogue)

	table = QTableWidget(num_rows, 6)
	table.setSortingEnabled(False)

	my_widget.table = table

	bold = QFont()
	bold.setBold(True)

	#table.setShowGrid(False)
	table.setSelectionBehavior(QAbstractItemView.SelectRows)

	sorted_headers = ["title", "year", "genre", "season", "episode"]

	headers = {"title": "Title", "year": "Year", "genre": "Genre", "season": "Season", "episode": "Episode" }

	#header
	header_col_index = 0

	for header in sorted_headers:

		header_item = QTableWidgetItem(headers[header])
		header_item.setFont(bold)

		table.setHorizontalHeaderItem(header_col_index, header_item)
		
		header_col_index = header_col_index + 1

	header_item = QTableWidgetItem("filename")
	header_item.setFont(bold)

	table.setHorizontalHeaderItem(header_col_index, header_item)

	
	#catalogue
	row_index = 0;

	filename_to_id = {}

	for movie_id in my_widget.catalogue:

		#f_name = catalogue[movie_id]["filename"]
		#print(movie_id, ":", f_name)

		table_item_id = QTableWidgetItem(str(movie_id))
		table.setItem(row_index, 5, table_item_id)

		col_index = 0

		for column in sorted_headers:

			column_val = str(my_widget.catalogue[movie_id][column])

			if (column_val == "None"):
				column_val = ""

			table_item = QTableWidgetItem(column_val)
			#table_item.setStyleSheet("color: white; background-color: black")

			table.setItem(row_index, col_index, table_item)


			col_index = col_index + 1

		row_index = row_index + 1

	table.setColumnHidden(5, True)

	#Autofit
	header = table.horizontalHeader()
	header.setSectionResizeMode(QHeaderView.ResizeToContents & QHeaderView.Stretch )


	#add click signal proc
	table.cellDoubleClicked.connect(row_clicked)
	table.setSortingEnabled(True)
	#hide id column
	#table_view = QTableView(table)
	#table_view.hideColumn(0)

	main_window.setCentralWidget(table)

def save_all_changes():

	save_changes()
	my_widget.unsaved_changes = False

	#print("display_movie()")
	#display_movie(my_widget.main_window, my_widget.current_movie)

'''User has changed the year'''
def year_changed(new_year):

	#print("year changed ", new_year)

	if ( re.match("^[0-9]{4}", new_year) ):
		my_widget.update_list["year"] = new_year
		my_widget.unsaved_changes = True
		#save_changes()
	else:
		my_widget.update_list["year"] = None

'''User has changed the season'''
def season_changed(new_season):

	if ( re.match("^[0-9]*$", new_season) ):
		my_widget.update_list["season"] = new_season
		my_widget.unsaved_changes = True
		#save_changes()
	else:
		my_widget.update_list["season"] = None

'''User has changed the episode'''
def episode_changed(new_episode):

	if ( re.match("^[0-9]*$", new_episode) ):
		#print("Episode changed")
		my_widget.update_list["episode"] = new_episode
		my_widget.unsaved_changes = True
		#save_changes()
	else:
		my_widget.update_list["episode"] = None

'''User has changed the title'''
def title_changed(new_title):

	my_widget.update_list["title"] = new_title
	my_widget.unsaved_changes = True

	#print("title changed ", new_title)

	#save_changes()

'''User has changed the description'''
def description_changed():

	new_text = my_widget.description_editor.toPlainText()
	my_widget.update_list["description"] = new_text
	my_widget.unsaved_changes = True
	#save_changes()

'''User has changed the genre'''
def genre_changed(new_genre):
	my_widget.update_list["genre"] = new_genre
	my_widget.unsaved_changes = True
	#save_changes()

'''Search Online for Movie Information'''
def search_online():

	my_widget.searched_online = True
	my_widget.unsaved_changes = True
	#save_changes()

	filename = my_widget.display_filename_field.text()
	title    = my_widget.display_title_field.text()
	year     = my_widget.display_year_field.text()
	season   = my_widget.display_season_field.text()
	episode  = my_widget.display_episode_field.text()
	genre    = my_widget.display_genre_field.text()

	if ( title == "" or year == "" ):

		parsed_filename = parse_filename(filename)

		if (title == ""):
			title = parsed_filename[0]
		if (year == ""):
			year = ""
			if ( parsed_filename[1] != "" ):
				year = parsed_filename[1]

	#check season/episode
	valid_request = True

	if ( season != "" or episode != ""):

		#must specify both
		if ( episode == "" or season == "" ):
			valid_request = False

			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)

			msg.setText("To search for a series, you must specify both a season and an episode")
			msg.setWindowTitle("Season or episode missing")
			msg.setStandardButtons(QMessageBox.Ok)
	
			retval = msg.exec_()


	movie_id = my_widget.current_movie

	if (valid_request):

		download_timer = QTimer()
		download_timer.setInterval(100)
		my_widget.download_timer = download_timer

		download_timer.timeout.connect(refresh_display)
		download_timer.start()

		my_thread = OMDbSearch(movie_id,title,year,season,episode,genre)
		my_widget.thread = my_thread

		my_thread.start();	
		
	#wemakesites_search(title,year)
'''Thread to run omdb_search'''
class OMDbSearch(QThread):
	
	def __init__(self, movie_id,title,year,season,episode,genre):

		QThread.__init__(self)
		self.movie_id = movie_id
		self.title = title
		self.year = year
		self.season = season
		self.episode = episode
		self.genre = genre

	def run(self):

		my_widget.main_window.setCursor(QCursor(Qt.WaitCursor))

		search_res = stoppable_omdb_search( self.movie_id, self.title, self.year, self.season, self.episode, self.genre, False)

		#print(search_res)
		my_widget.main_window.setCursor(QCursor(Qt.ArrowCursor))

		#print("search_results:", search_res)

		#sometimes this thread returns long after
		#the user has moved on
		if (search_res["movie_id"] == my_widget.current_movie):

			my_widget.search_results = search_res
			my_widget.update_list = search_res

			my_widget.download_complete = True
			my_widget.search_stopped = False


		#display_movie(my_widget.main_window, self.movie_id)


'''Play Movie'''
def play_movie():

	movie_id = my_widget.current_movie
	catalogue = my_widget.catalogue

	is_eyetv = False

	filename = catalogue[movie_id]["filename"]

	for file_extension in [".eyetv", ".eyetv.zip"]:

		ext_len = len(file_extension)
		file_n_tail = filename[-ext_len:]

		if (file_extension == file_n_tail.lower()):
			is_eyetv = True
			break

	if (is_eyetv):

		eyetv_movies_dir = read_conf("eyetv_movies_directory")
		if ( eyetv_movies_dir != None ):

			#check eyetv movies directory for this file
			files = listdir(eyetv_movies_dir)
			id_dot = movie_id + "."

			for file_n in files:
				if (file_n.find(id_dot) == 0):
					filename = join(eyetv_movies_dir, file_n)

	player = read_conf("player")
	
	if ( player != None ):
		args = shlex.split("%s '%s'" % (player, filename,) )
		subprocess.Popen(args)

	else:
		#show dialog box warning that
		#the player has not been configured
		error_dialog = QErrorMessage()
		error_dialog.showMessage("The default movie player has not been configured.")

		pass


'''Save changes'''
def save_changes():

	update_list = my_widget.update_list
	movie_id = my_widget.current_movie

	update_movie_fields(update_list, movie_id)

	my_widget.update_list = {}

'''Delete Entry from List'''
def delete_entry():

	msg = QMessageBox()
	msg.setIcon(QMessageBox.Question)

	msg.setText("Are you sure you want to delete this entry?")
	msg.setWindowTitle("Delete entry")
	msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
	
	retval = msg.exec_()

	if (retval == QMessageBox.Ok):

		movie_id = my_widget.current_movie
		delete_movie(movie_id)
	
		back()

'''Cancel download op or discard downloaded info'''
def cancel_operation():

	if ( my_widget.searched_online ):

		#stop ongoing download
		#if (not my_widget.download_complete ):
		#	pass
		my_widget.main_window.setCursor(QCursor(Qt.ArrowCursor))
		my_widget.search_stopped = True

	#restore old cover picture, movie info and crews data
	restore_movie(my_widget.current_movie)

	#display this old data
	display_movie(my_widget.main_window, my_widget.current_movie)

	my_widget.unsaved_changes = False
	#print("Cancelling op...")
	#pass

'''Remove ads from the movie'''
def remove_adverts():

	widget = QWidget()
	widget.setMaximumHeight(200)

	grid = QGridLayout()

	progress_bar_pt = 0	
	progress_bar = QProgressBar()
	progress_bar.setGeometry(30,40,200, 25)

	grid.addWidget(progress_bar, 0,0)

	label = QLabel("")
	grid.addWidget(label, 1, 0)

	widget.setLayout(grid)

	grid.setAlignment(progress_bar, Qt.AlignVCenter)
	#grid.setAlignment(progress_bar, Qt.AlignHCenter)

	grid.setAlignment(label, Qt.AlignTop)
	#grid.setAlignment(label, Qt.AlignHCenter)

	window = my_widget.main_window;
	window.setCentralWidget(widget)

	total_files = int(read_conf("num_files"))

	my_widget.ad_remover_progress_bar = progress_bar
	my_widget.ad_remover_progress_label = label

	#launch subprocess
	subprocess.Popen( ["python2", "remover.py"], shell=False,stdin=None,stdout=None,stderr=None,close_fds=True )

	#launch timer to check progress
	timer = QTimer()
	timer.setInterval(500)
	my_widget.ad_remover_timer = timer

	timer.timeout.connect(check_ad_remover_progress)
	timer.start()

def check_ad_remover_progress():

	#read stage
	stage = read_conf("ad_remover_stage")
	
	if (not stage == None):

		#reading ads
		if ( stage == "0" ):

			f_name = read_conf("ad_remover_file")
			if (f_name == None):
				f_name = "movie"

			ads_seen = read_conf("ads_seen")
			if (ads_seen == None):
				ads_seen = "0"

			my_widget.ad_remover_progress_label.setText("Processing movie %s. Seen %s ads so far..." % (f_name, ads_seen))

			complete = read_conf("ad_remover_complete")
			if (complete == None):
				complete = "0"

			my_widget.ad_remover_progress_bar.setValue(int(complete))

			pass

		#clipping
		elif (stage == "1"):
			my_widget.ad_remover_progress_label.setText("Clipping movie to remove ads...")

		#done
		elif ( stage == "2" ):

			my_widget.ad_remover_progress_label.setText("Done removing ads!")

			#stop ad remover
			my_widget.ad_remover_timer.stop()

	pass

'''Display movie information and play the movie'''
def display_movie(main_window, movie_id):

	#print("Displaying movie", movie_id)
	catalogue = my_widget.catalogue

	movie_poster_file = "blank_movie_poster.png";

	if ( catalogue[movie_id]["cover_picture"] != None ):

		cover_pic = catalogue[movie_id]["cover_picture"]

		if ( exists(cover_pic) ):
			movie_poster_file = cover_pic


	my_widget.current_movie = movie_id

	grid = QGridLayout()
	display_widget = QWidget()	

	display_widget.setLayout(grid)

	#add buttons
	#<Online Search> <Play> <Save Changes>
	buttons_widget = QWidget()
	buttons_layout = QVBoxLayout()
	
	#buttons_layout.addStretch()
	buttons_widget.setLayout(buttons_layout)
	
	#Online Search
	online_search_pixmap = QPixmap("web-icon.png")
	online_search_pixmap = online_search_pixmap.scaledToHeight(128)

	online_search_icon = QIcon(online_search_pixmap)

	online_search_button = QToolButton()
	online_search_button.setIcon(online_search_icon)
	online_search_button.setIconSize(QSize(64, 64))

	online_search_action = QAction(online_search_icon, "Search Online For Movie Information", online_search_button)
	online_search_button.setDefaultAction(online_search_action)

	online_search_button.triggered.connect(search_online)

	buttons_layout.addWidget(online_search_button)

	#Play
	play_pixmap = QPixmap("play-icon.png")

	play_icon = QIcon(play_pixmap)

	play_button = QToolButton()
	play_button.setIcon(play_icon)
	play_button.setIconSize(QSize(64, 64))

	play_action = QAction(play_icon, "Play Movie Using the Configured Player", play_button)
	play_button.setDefaultAction(play_action)
	play_action.triggered.connect(play_movie)

	buttons_layout.addWidget(play_button)

	#Save Changes
	save_pixmap = QPixmap("save-icon.png")

	save_icon = QIcon(save_pixmap)

	save_button = QToolButton()
	save_button.setIcon(save_icon)
	save_button.setIconSize(QSize(64, 64))

	save_action = QAction(save_icon, "Save Changes to Movie Information", save_button)
	save_button.setDefaultAction(save_action)
	save_action.triggered.connect(save_all_changes)

	buttons_layout.addWidget(save_button)	

	#Delete Movie
	delete_pixmap = QPixmap("delete-icon.png")

	delete_icon = QIcon(delete_pixmap)

	delete_button = QToolButton()
	delete_button.setIcon(delete_icon)
	delete_button.setIconSize(QSize(64, 64))

	delete_action = QAction(delete_icon, "Delete Entry from Catalogue", delete_button)
	delete_button.setDefaultAction(delete_action)
	delete_action.triggered.connect(delete_entry)

	buttons_layout.addWidget(delete_button)	

	#Stop/Cancel
	cancel_pixmap = QPixmap("cancel-icon.png")

	cancel_icon = QIcon(cancel_pixmap)

	cancel_button = QToolButton()
	cancel_button.setIcon(cancel_icon)
	cancel_button.setIconSize(QSize(64, 64))

	cancel_action = QAction(cancel_icon, "Cancel Operation", cancel_button)
	cancel_button.setDefaultAction(cancel_action)
	cancel_action.triggered.connect(cancel_operation)

	buttons_layout.addWidget(cancel_button)

	#Remove ads
	ads_pixmap = QPixmap("ads-icon.png")

	ads_icon = QIcon(ads_pixmap)

	ads_button = QToolButton()
	ads_button.setIcon(ads_icon)
	ads_button.setIconSize(QSize(64, 64))

	ads_action = QAction(ads_icon, "Remove Ads", ads_button)
	ads_button.setDefaultAction(ads_action)
	ads_action.triggered.connect(remove_adverts)

	buttons_layout.addWidget(ads_button)


	buttons_layout.addStretch()


	grid.addWidget(buttons_widget, 0, 0, 8, 1)
	
	window_width = main_window.width()

	pics_dir = read_conf("pictures_directory")
	id_len = len(movie_id)

	#add poster
	poster_label = QLabel()
	poster_pixmap = QPixmap(movie_poster_file)	
	poster_pixmap = poster_pixmap.scaledToWidth((window_width *0.4))

	poster_label.setPixmap(poster_pixmap)

	my_widget.poster_label = poster_label
	
	grid.addWidget(poster_label,0, 1, 8, 1)
	grid.setAlignment(poster_label, Qt.AlignVCenter)

	#grid.setStyleSheet("")

	#add movie information
	sorted_headers = ["filename", "title", "year", "genre", "description", "season", "episode"]

	headers = {"filename": "Filename", "title": "Title", "year": "Year", "genre": "Genre", "description": "Description", "season": "Season", "episode": "Episode"}

	genres = ["Absurdist/Surreal/Whimsical","Action","Adventure","Comedy","Crime","Drama","Fantasy","Historical","Historical fiction","Horror","Magical realism","Mystery","Paranoid","Philosophical","Political","Romance","Saga","Satire","Science fiction","Slice of Life","Speculative","Thriller","Urban","Western","Animation","Live-action scripted","Live-action unscripted"]

	catalogue = read_entire_catalogue(None)
	my_widget.catalogue = catalogue

	#print(len(catalogue.keys()))

	bold = QFont()
	bold.setBold(True)

	row_index = 0
	#row_index = 1
	for header in sorted_headers:

		column_val = str(catalogue[str(movie_id)][header])

		if ( column_val == "None" ):
			column_val = ""

		label = QLabel(str(headers[header]) + ":")
		label.setStyleSheet("border: none");
		label.setAlignment(Qt.AlignTop)

		label.setFont(bold)

		grid.addWidget(label, row_index, 2)

		if (header == "description"):

			val = QTextEdit(column_val)
			my_widget.description_editor = val
			my_widget.description_editor.setStyleSheet("border: none")
			my_widget.description_editor.textChanged.connect(description_changed)
			grid.addWidget(my_widget.description_editor, row_index, 3)

		#elif ( header == "filename" ):
		#	val = QLabel(column_val)
		#	my_widget.display_filename_field = val
			
		else:
			val = QLineEdit(column_val);

			if (header == "title"):
				my_widget.display_title_field = QLineEdit(column_val)
				my_widget.display_title_field.setStyleSheet("border: none")
				my_widget.display_title_field.textChanged.connect(title_changed)
				grid.addWidget(my_widget.display_title_field, row_index, 3)

			elif (header == "year"):
				my_widget.display_year_field = QLineEdit(column_val)
				my_widget.display_year_field.setStyleSheet("border: none")
				my_widget.display_year_field.textChanged.connect(year_changed)
				grid.addWidget(my_widget.display_year_field, row_index, 3)

			elif (header == "season"):
				my_widget.display_season_field = QLineEdit(column_val)
				my_widget.display_season_field.setStyleSheet("border: none")
				my_widget.display_season_field.textChanged.connect(season_changed)
				grid.addWidget(my_widget.display_season_field, row_index, 3)

			elif (header == "episode"):
				my_widget.display_episode_field = QLineEdit(column_val)
				my_widget.display_episode_field.setStyleSheet("border: none")
				my_widget.display_episode_field.textChanged.connect(episode_changed)
				grid.addWidget(my_widget.display_episode_field, row_index, 3)

			elif (header == "genre"):
				my_widget.display_genre_field = QLineEdit(column_val)
				my_widget.display_genre_field.setStyleSheet("border: none")
				my_widget.display_genre_field.textChanged.connect(genre_changed)
				grid.addWidget(my_widget.display_genre_field, row_index, 3)

			elif (header == "filename"):

				f_name = QLineEdit(column_val)
				my_widget.display_filename_field = f_name
				my_widget.display_filename_field.setStyleSheet("border: none")
				grid.addWidget(f_name, row_index, 3)


		row_index = row_index + 1

	#blank_label = QLabel("")

	#grid.addWidget(crews_label, row_index, 0, 1, 4)
	#grid.setAlignment(crews_label, Qt.AlignHCenter)
	
	#row_index = row_index + 1

	
	crews_label = QLabel("Crews")
	crews_label.setFont(bold)

	grid.addWidget(crews_label, row_index + 1, 0, 2, 4)
	grid.setAlignment(crews_label, Qt.AlignHCenter)

	row_index = row_index + 3

	#Crews Table
	crews = read_entire_crew(movie_id)

	my_widget.crews = crews

	crews_table = build_crews_table(crews)

	crews_table.setStyleSheet("border: 1px dashed white")

	my_widget.grid = grid
	my_widget.crews_table = crews_table

	grid.addWidget(crews_table, row_index, 0, 1, 4)

	#my_widget.crews_table = crews_table

	scroll = QScrollArea()
	scroll.setWidget(display_widget)

	#scroll.setStyleSheet("background-image: url(" + movie_poster_file + "); background-repeat: no-repeat")

	main_window.setCentralWidget(scroll)
	
'''return a QWidget with the crew info'''

def build_crews_table(crews):

	bold = QFont()
	bold.setBold(True)

	crews_table = QTableWidget(len(crews.keys()), 4)

	#headers = ["name": "Name", "role": "Role", "Stage_name": row[3], "biography": row[4], "picture": row[5]}

	#picture
	header_item = QTableWidgetItem("Picture")
	header_item.setFont(bold)

	crews_table.setHorizontalHeaderItem(0, header_item)

	#name
	header_item = QTableWidgetItem("Name")
	header_item.setFont(bold)

	crews_table.setHorizontalHeaderItem(1, header_item)

	#role
	header_item = QTableWidgetItem("Role")
	header_item.setFont(bold)

	crews_table.setHorizontalHeaderItem(2, header_item)

	#stage name
	header_item = QTableWidgetItem("Stage Name")
	header_item.setFont(bold)

	crews_table.setHorizontalHeaderItem(3, header_item)

	crew_row_index = 0;

	for crew in sorted(crews.keys(), key=lambda crew_id: crews[crew_id]["role"][0:2] + crews[crew_id]["first_name"][0:2]):

		picture = crews[crew]["picture"]

		if ( picture == None ):
			picture = "nopic-icon.png"

		pic_label = QLabel()

		pic = QPixmap(picture)
		pic = pic.scaledToHeight(32)

		pic_label.setPixmap(pic)

		crews_table.setCellWidget(crew_row_index, 0, pic_label)

		name_item = QTableWidgetItem(crews[crew]["name"])
		crews_table.setItem(crew_row_index, 1, name_item)

		role = crews[crew]["role"]
		if (role == None):
			role = ""

		role_item = QTableWidgetItem(role)
		crews_table.setItem(crew_row_index, 2, role_item)

		stage_name = crews[crew]["stage_name"]
		if (stage_name == None):
			stage_name = ""

		stage_name_item = QTableWidgetItem(stage_name)
		crews_table.setItem(crew_row_index, 3, stage_name_item)

		crew_row_index = crew_row_index + 1

	crews_header = crews_table.horizontalHeader()
	crews_header.setSectionResizeMode(QHeaderView.Stretch & QHeaderView.ResizeToContents)

	crews_table.setSelectionBehavior(QAbstractItemView.SelectRows)

	crews_table.cellDoubleClicked.connect(crews_row_clicked)

	#my_widget.crews_table = crews_table

	return crews_table


'''Clicked a row in the crews table'''
def crews_row_clicked(row, col):
	
	crews_table = my_widget.crews_table

	clicked_item = crews_table.item(row, 1)	

	if (clicked_item != None):

		name = clicked_item.text()	
		display_crew(my_widget.current_movie, name)


'''Display the cast member'''
def display_crew(movie_id, name):

	#print("Displaying %s: %s" % (movie_id, name))

	selected_crew = None

	crews = my_widget.crews

	for crew_id in crews:
		if ( crews[crew_id]["name"] == name ):
			selected_crew = crew_id
			#print("Seen crew %s: %s" % (crew_id, name))

	if (selected_crew != None):

		main_win = my_widget.main_window
		pic_width = main_window.width() * 0.6

		grid = QGridLayout()

		#picture
		pic = crews[selected_crew]["picture"]

		poster_label = QLabel()
		poster_pixmap = QPixmap(pic)
	
		if ( poster_pixmap.width() > pic_width ):
			poster_pixmap = poster_pixmap.scaledToWidth(pic_width)

		poster_label.setPixmap(poster_pixmap)
		
		grid.addWidget(poster_label,0, 0)
		#grid.setAlignment(poster_label, Qt.AlignVCenter)


		#name
		#name_label = QLabel("<b>Name:</b>" + crews[selected_crew]["name"])

		#grid.addWidget(name_label,0, 1)
		#grid.setAlignment(name_label, Qt.AlignVCenter)

		bio_label = QLabel("Biography")

		#grid.addWidget(bio_label,1, 1)
		#grid.setAlignment(bio_label, Qt.AlignVCenter)

		name = crews[selected_crew]["name"]
		if (name == None):
			name = ""

		biog = crews[selected_crew]["biography"]
		if (biog == None):
			biog = ""

		bio_str = "<p>" + "<b>Name: </b>" + name + "<p>" + biog

		bio_str = bio_str.replace("Date of Birth", "<b>Date of Birth: </b>", 1)
		bio_str = bio_str.replace("Height", "<b>Height: </b>", 1)
		bio_str = bio_str.replace("Birth Name", "<b>Birth Name: </b>", 1)
		bio_str = bio_str.replace("Nickname", "<b>Nickname: </b>", 1)

		bio_str = bio_str.replace("\n", "<p>")
		bio_field = QTextEdit(bio_str)

		grid.addWidget(bio_field, 0, 1)
		#grid.setAlignment(bio_field, Qt.AlignVCenter)
	
		widget = QWidget()
		widget.setLayout(grid)

		main_window.setCentralWidget(widget)
		
		my_widget.displaying_crew = True

'''Go back in the menu'''
def back():

	#warn about unsaved changes
	go_back_ok = True

	if ( my_widget.unsaved_changes ):

		go_back_ok = False

		msg = QMessageBox()
		msg.setIcon(QMessageBox.Question)

		msg.setText("You have not saved the changes. Are you sure you want to discard these changes?")
		msg.setWindowTitle("Discard Changes")
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
	
		retval = msg.exec_()

		if ( retval == QMessageBox.Ok ):
			go_back_ok = True

	if ( go_back_ok ):

		if (my_widget.unsaved_changes and my_widget.searched_online):
			restore_movie(my_widget.current_movie)

		#close fields
		if (my_widget.display_title_field != None):

			if ( not sip.isdeleted(my_widget.display_title_field) ):
				my_widget.display_title_field.close()

			my_widget.display_title_field = None

		if (my_widget.display_year_field != None):

			if ( not sip.isdeleted(my_widget.display_year_field) ):
				my_widget.display_year_field.close()

			my_widget.display_year_field  = None

		if (my_widget.display_season_field != None):
			if ( not sip.isdeleted(my_widget.display_season_field) ):
				my_widget.display_season_field.close()

			my_widget.display_season_field = None

		if (my_widget.display_episode_field != None):
			if ( not sip.isdeleted(my_widget.display_episode_field)):
				my_widget.display_episode_field.close()

			my_widget.display_season_field = None

		if (my_widget.display_filename_field != None):
			if ( not sip.isdeleted(my_widget.display_filename_field) ):
				my_widget.display_filename_field.close()

			my_widget.display_filename_field= None


		my_widget.unsaved_changes = False
		my_widget.searched_online = False

		if ( my_widget.download_timer != None ):

			my_widget.download_timer.stop()
			my_widget.download_timer = None

		#reset cursor
		my_widget.main_window.setCursor(QCursor(Qt.ArrowCursor))

		if ( my_widget.displaying_crew ):	
			my_widget.displaying_crew = False
			display_movie(my_widget.main_window, my_widget.current_movie)
		else:
			load_catalogue(my_widget.main_window, None)

def go_home():
	load_catalogue(my_widget.main_window, None)
	
def load_toolbar(main_window):

	#Go Back
	backAction = QAction(QIcon('back-icon.png'), 'Back', main_window)
	backAction.setStatusTip('Go Back')
	backAction.triggered.connect(back)

	main_window.toolbar = main_window.addToolBar('Back')
	main_window.toolbar.addAction(backAction)

	#Home Button
	homeAction = QAction(QIcon('home-icon.png'), 'Home', main_window)
	homeAction.setStatusTip('Go to the home screen')
	homeAction.triggered.connect(go_home)

	main_window.toolbar = main_window.addToolBar('Home')
	main_window.toolbar.addAction(homeAction)


	#Search
	searchAction = QAction(QIcon('search-icon.png'), 'Search', main_window)
	searchAction.setShortcut('Ctrl+F')
	searchAction.setStatusTip('Search Catalogue')
	searchAction.triggered.connect(search)
        
	main_window.toolbar = main_window.addToolBar('Search')
	main_window.toolbar.addAction(searchAction)
       
	#Settings
	settingsAction = QAction(QIcon('settings-icon.png'), 'Settings', main_window)	
	settingsAction.setStatusTip('Settings')
	settingsAction.triggered.connect(settings)
        
	main_window.toolbar = main_window.addToolBar('Settings')
	main_window.toolbar.addAction(settingsAction)

	#Scan
	scanAction = QAction(QIcon('scan-icon.png'), 'Scan', main_window)	
	scanAction.setStatusTip('Scan filesystem for movies')
	scanAction.triggered.connect(scan)
        
	main_window.toolbar = main_window.addToolBar('Scan')
	main_window.toolbar.addAction(scanAction)

	my_widget.runs = my_widget.runs + 1

def stoppable_omdb_search(movie_id, title, year=None, season=None, episode=None, search_genre=None, do_update=False):

	updates = { "movie_id": movie_id }

	if (title == None):
		return updates

	quoted_title = urllib.parse.quote(title)

	url = "http://www.omdbapi.com/?s=" + quoted_title

	if ( year != None and year != ""):
		url += "&y=" + urllib.parse.quote(year)
		updates["year"] = year

	url += "&plot=full"

	series = False

	if ( season != None and season != "" and episode != None and episode != "" ):
		url += "&type=series"
		series = True

		updates["season"] = season
		updates["episode"] = episode


	else:
		url += "&type=movie"

	response = ""

	try:
		with urllib.request.urlopen(url) as f:
			for line in f.readlines():
				response += line.decode("utf-8")

	except urllib.request.URLError:
		return updates
	except UnicodeEncodeError:
		return updates

	#check stop
	if (my_widget.search_stopped):
		return {}

	if (len(response) == 0):
		return updates

	data = json.loads(response)

	imdb_id = None
	saved_title = title

	try:
		search_results = data["Search"]

		#search by genre
		selected_index = 0

		if ( len(search_results) > 1 ):

			if (search_genre != None):

				for search_result in range(len(search_results)):

					search_selection = search_results[search_result]

					try:
						imdb_id = search_selection["imdbID"]

						response = ""

						search_url = "http://www.omdbapi.com/?i=" + imdb_id

						try:

							with urllib.request.urlopen(search_url) as f:
								for line in f.readlines():
									response += line.decode("utf-8")


							search_selection_data = json.loads(response)
							search_selection_genre = search_selection_data["Genre"]

							if (search_selection_genre.lower().find(search_genre.lower()) >= 0):
								selected_index = search_result
								break

						except urllib.request.URLError:
							pass
						except UnicodeEncodeError:
							pass
						except KeyError:
							pass
						#check stop
						if (my_widget.search_stopped):
							return {}


					except KeyError:
						pass
		

		selection = search_results[selected_index]

		#print(selection)

		try:
			imdb_id = selection["imdbID"]

			response = ""

			url = "http://www.omdbapi.com/?i=" + imdb_id

			try:

				with urllib.request.urlopen(url) as f:
					for line in f.readlines():
						response += line.decode("utf-8")

			except urllib.request.URLError:
				return updates
			except UnicodeEncodeError:
				return updates

			#check stop
			if (my_widget.search_stopped):
				return {}

			selection = json.loads(response)

			saved_title = selection["Title"]
			if (do_update):
				update_catalogue(movie_id, "title", saved_title)
			else:
				updates["title"] = saved_title

			yr = selection["Year"]

			if (do_update):
				update_catalogue(movie_id, "year", yr)
			else:
				updates["year"] = yr

			genre = selection["Genre"]

			if (do_update):
				update_catalogue(movie_id, "genre", genre)
			else:
				updates["genre"] = genre

			#get poster
			poster_url = selection["Poster"]
			poster_url = poster_url.replace("_SX300.", ".")

			if ( re.match("^https?://", poster_url, re.IGNORECASE) ):

				extension = ""
				ext_index = poster_url.rfind(".")

				if (ext_index >= 0):
					extension = poster_url[poster_url.rfind("."):]

				out_file_dir = read_conf("pictures_directory")
				out_file_dir = join(out_file_dir, "full")

				out_file = join(out_file_dir, str(movie_id) + extension)

				if ( not do_update ):

					#copy file
					if ( exists(out_file)):
						copy(out_file, out_file + "_dup")

				pic_file = open(out_file, "w+b")

				try:
					with urllib.request.urlopen(poster_url) as f:
						for line in f:
							pic_file.write(line)

					if (do_update):
						update_catalogue(movie_id, "cover_picture", out_file)
					else:
						#copy file
						updates["cover_picture"] = out_file

				except URLError:
					pass

				#check stop
				if (my_widget.search_stopped):
					return {}

			description = selection["Plot"]
			
			if ( do_update ):
				update_catalogue(movie_id, "description", description)
			else:
				updates["description"] = description

			all_crew = {}

			cast = selection["Actors"]
			for cast_member in cast.split(","):	
				all_crew[cast_member] = "cast"


			directors = selection["Director"]
			for director in directors.split(","):
				all_crew[director] = "director"


			writers = selection["Writer"]
			for writer in writers.split(","):
				all_crew[writer] = "writer"

			if ( not do_update ):
				#backup crew(both metadata and pics)
				#before replacing it
				#print("calling backup crew")
				backup_crew(movie_id)

				pass

			update_crew(movie_id, all_crew)

		except KeyError:
			pass

	except KeyError:
		pass

	driver = None
	
	if (imdb_id != None):
		driver = webdriver.PhantomJS(service_args=["--load-images=no"])

	if ( series and imdb_id != None ):

		#read imdb.com for list of episodes
		response = ""

		seasons_url = "http://www.imdb.com/title/%s/episodes?season=%s" % (imdb_id, season);	

		driver.get(seasons_url);
		#check stop
		if (my_widget.search_stopped):
			return {}

		page = driver.find_element_by_tag_name("body").text

		lines = page.split("\n")

		found = False
		description = ""

		cntr = 0
	
		season_episode_re = re.compile("^\s*S([0-9]+),\s*Ep([0-9]+)$")

		for line in lines:

			matched = season_episode_re.match(line)

			if (matched):

				if (found):
					break

				else:
					cntr = 0
					matched_season  = matched.group(1)
					matched_episode = matched.group(2)

					if ( matched_season == season and matched_episode == episode ):
						found = True
			elif (found):

				if (cntr == 0):
					description = "Aired on " + line + ". "
					cntr = cntr + 1	

				elif (cntr == 1):
					new_title = saved_title + "(" + line + ")"

					if (do_update):
						update_catalogue(movie_id, "title", new_title)
					else:
						updates["title"] = new_title

					cntr = cntr + 1

				else:
					description += line + ". "
			
		if ( description != "" ):
			if (do_update):
				update_catalogue(movie_id, "description", description)
			else:
				updates["description"] = description

	#full cast
	if ( imdb_id != None ):

		seasons_url = "http://www.imdb.com/title/%s/fullcredits" % (imdb_id,);

		#print(seasons_url)

		driver.get(seasons_url);

		#check stop
		if (my_widget.search_stopped):
			return {}

		page = driver.find_element_by_tag_name("body").text

		lines = page.split("\n")

		in_cast = False
		expect_stage_name = False
		cast_member = ""

		cast_cntr = 0;

		cast_pattern = re.compile("^(Series\s+)?Cast", re.IGNORECASE)
		cast_member_pattern = re.compile("^([\w\s\-]+)\s+\.\.\.")
		stage_name_pattern  = re.compile("^\s*([\w\s\-]+)")

		cast = {}
		#print("Further search for %s yielded %d: " % (imdb_id,len(lines)), cast)

		for line in lines:

			if (in_cast):

				if ( expect_stage_name ):

					matched_stage_name = stage_name_pattern.match(line)

					if ( matched_stage_name ):

						stage_name = matched_stage_name.group(1)
						cast[cast_member]["stage_name"] = stage_name

						cast_cntr = cast_cntr + 1
						expect_stage_name = False

						if ( cast_cntr > 10 ):
							break

					else:
						break

				else:
					matched_cast_member = cast_member_pattern.match(line)

					if ( matched_cast_member ):

						cast_member = matched_cast_member.group(1)
						cast[cast_member] = { "stage_name": None, "biography": None, "picture": None }

						expect_stage_name = True

					else:
						break
					
			elif (cast_pattern.match(line)):
				in_cast = True

		imdb_nm_pattern = re.compile("/name/([^/]+)/")

		overview_pattern = re.compile("^Overview", re.IGNORECASE)
		bio_pattern = re.compile("^Mini\s+Bio", re.IGNORECASE)


		for member in cast:
			try:

				link = driver.find_element_by_link_text(member)
				ref = link.get_property("href")

				matched_imdb_nm = imdb_nm_pattern.search(ref)
				character_id = None

				if ( matched_imdb_nm ):
					character_id = matched_imdb_nm.group(1)	

				if ( character_id != None ):

					link.click()
					pic = driver.find_element_by_id("name-poster")

					addr = pic.get_property("src")

					#download picture
					out_file_dir = read_conf("pictures_directory")
					out_file_dir = join(out_file_dir, "thumbnails")

					out_file = join(out_file_dir, character_id + ".jpg")

					pic_file = open(out_file, "w+b")

					with urllib.request.urlopen(addr) as f:
						for line in f:
							pic_file.write(line)

					#save picture
					cast[member]["picture"] = out_file

					#get bio
					bio = ""

					driver.get("http://www.imdb.com/name/%s/bio" % (character_id, ))

					#check stop
					if (my_widget.search_stopped):
						return {}

					page = driver.find_element_by_tag_name("body").text
					lines = page.split("\n")
	
					in_mini_bio = False
					in_bio = False

					for line in lines:
						if ( overview_pattern.match(line) ):
							in_bio = True
							continue

						elif ( bio_pattern.match(line) ):
							in_mini_bio = True
							continue

						if (in_bio):	
							bio += line + os.linesep 

						if (in_mini_bio):
							break

					cast[member]["biography"] = bio

					#go back from the /bio page
					driver.back()
				#go back to /fullcredits
				driver.back()

			except NoSuchElementException as exc:
				pass

		update_cast(movie_id, cast)

	return updates

if __name__ == '__main__':

	runs = 0;
    
	app = QApplication(sys.argv)

	main_window = QMainWindow()

	main_window.setStyleSheet(open("modern_look.qss", "r").read())
	#main_window.setAutoFillBackground(True) 

	main_window.resize(900, 540)

	#center
	qr = main_window.frameGeometry()
	cp = QDesktopWidget().availableGeometry().center()
	qr.moveCenter(cp)

	main_window.move(qr.topLeft())

	main_window.setWindowTitle('Movie Catalogue')
	
	load_toolbar(main_window)

	my_widget.main_window = main_window
	
	#load initial display
	load_catalogue(main_window, None)

	main_window.show()
    
	sys.exit(app.exec_())

