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

'''Process clicked row'''
def row_clicked(row, col):

	table = my_widget.table
	header = table.verticalHeaderItem(row) 
	
	movie_id = header.text()
	
	print("Displaying info about movie %s" % movie_id)
	display_movie(my_widget.main_window, movie_id)
	print("Displayed info about movie %s" % movie_id)

'''Display the entries in the catalogue'''
def load_catalogue(main_window,search_params):

	catalogue = read_entire_catalogue(search_params)

	my_widget.catalogue = catalogue

	num_rows = len(catalogue)

	table = QTableWidget(num_rows, 5)
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

	#catalogue
	row_index = 0;

	for movie_id in catalogue:

		table.setVerticalHeaderItem(row_index, QTableWidgetItem(str(movie_id)))

		col_index = 0

		for column in headers.keys():

			column_val = str(catalogue[movie_id][column])
			if (column_val == "None"):
				column_val = ""

			table_item = QTableWidgetItem(str(column_val))
			table.setItem(row_index, col_index, table_item)

			col_index = col_index + 1

		row_index = row_index + 1

	#Autofit
	header = table.horizontalHeader()
	header.setSectionResizeMode(QHeaderView.ResizeToContents & QHeaderView.Stretch )

	#table.setSortingEnabled(True)
	#add click signal proc
	table.cellDoubleClicked.connect(row_clicked)

	#hide id column
	#table_view = QTableView(table)
	#table_view.hideColumn(0)

	main_window.setCentralWidget(table)

def save_all_changes():

	save_changes()
	display_movie(my_widget.main_window, my_widget.current_movie)

'''User has changed the year'''
def year_changed(new_year):

	if ( re.match("^[0-9]{4}$", new_year) ):
		my_widget.update_list["year"] = new_year
		save_changes()
	else:
		my_widget.update_list["year"] = None

'''User has changed the season'''
def season_changed(new_season):

	if ( re.match("^[0-9]*$", new_season) ):
		my_widget.update_list["season"] = new_season
		save_changes()
	else:
		my_widget.update_list["season"] = None

'''User has changed the episode'''
def episode_changed(new_episode):

	if ( re.match("^[0-9]*$", new_episode) ):
		my_widget.update_list["episode"] = new_episode
		save_changes()
	else:
		my_widget.update_list["episode"] = None

'''User has changed the title'''
def title_changed(new_title):

	my_widget.update_list["title"] = new_title
	save_changes()

'''User has changed the description'''
def description_changed():

	new_text = my_widget.description_editor.toPlainText()
	my_widget.update_list["description"] = new_text
	save_changes()

'''User has changed the genre'''
def genre_changed(new_genre):
	my_widget.update_list["genre"] = new_genre
	save_changes()

'''Search Online for Movie Information'''
def search_online():

	filename = my_widget.display_filename_field.text()
	title    = my_widget.display_title_field.text()
	year     = my_widget.display_year_field.text()
	season   = my_widget.display_season_field.text()
	episode  = my_widget.display_episode_field.text()

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

		my_thread = OMDbSearch(movie_id,title,year,season,episode)
		my_thread.start();

	display_movie(my_widget.main_window, movie_id)

	#wemakesites_search(title,year)
'''Thread to run omdb_search'''
class OMDbSearch(QThread):
	
	def __init__(self, movie_id,title,year,season,episode):

		QThread.__init__(self)
		self.movie_id = movie_id
		self.title = title
		self.year = year
		self.season = season
		self.episode = episode


	def run(self):

		my_widget.main_window.setCursor(QCursor(Qt.WaitCursor))
		omdb_search( self.movie_id, self.title, self.year, self.season, self.episode)
		my_widget.main_window.setCursor(QCursor(Qt.ArrowCursor))

'''omdb_search'''
def run_omdb_search(movie_id,title,year,season,episode):
	print("Called omdb_search()")
	omdb_search(movie_id,title,year,season,episode)


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
		subprocess.getoutput('%s "%s"' % (player, filename))

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
	
'''Display movie information and play the movie'''
def display_movie(main_window, movie_id):

	#print("Displaying movie", movie_id)

	my_widget.current_movie = movie_id

	grid = QGridLayout()
	display_widget = QWidget()

	display_widget.setLayout(grid)

	#add buttons
	#<Online Search> <Play> <Save Changes>
	buttons_widget = QWidget()
	buttons_layout = QHBoxLayout()
	
	buttons_layout.addStretch()
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
	buttons_layout.addStretch()

	catalogue = my_widget.catalogue

	grid.addWidget(buttons_widget, 0, 0, 1, 2)
	
	window_width = main_window.width()

	movie_poster_file = "blank_movie_poster.png";

	if ( catalogue[movie_id]["cover_picture"] != None ):

		cover_pic = catalogue[movie_id]["cover_picture"]

		if ( exists(cover_pic) ):
			movie_poster_file = cover_pic

	pics_dir = read_conf("pictures_directory")
	id_len = len(movie_id)

	#add poster
	poster_label = QLabel()
	poster_pixmap = QPixmap(movie_poster_file)	
	poster_pixmap = poster_pixmap.scaledToWidth((window_width *0.6))

	poster_label.setPixmap(poster_pixmap)
	
	grid.addWidget(poster_label,1, 0,1,2)
	grid.setAlignment(poster_label, Qt.AlignVCenter)

	#add movie information
	sorted_headers = ["filename", "title", "year", "genre", "description", "season", "episode"]

	headers = {"filename": "Filename", "title": "Title", "year": "Year", "genre": "Genre", "description": "Description", "season": "Season", "episode": "Episode"}

	genres = ["Absurdist/Surreal/Whimsical","Action","Adventure","Comedy","Crime","Drama","Fantasy","Historical","Historical fiction","Horror","Magical realism","Mystery","Paranoid","Philosophical","Political","Romance","Saga","Satire","Science fiction","Slice of Life","Speculative","Thriller","Urban","Western","Animation","Live-action scripted","Live-action unscripted"]

	#print(len(catalogue.keys()))

	bold = QFont()
	bold.setBold(True)

	row_index = 2

	for header in sorted_headers:

		column_val = str(catalogue[str(movie_id)][header])

		if ( column_val == "None" ):
			column_val = ""

		label = QLabel(str(headers[header]))
		label.setFont(bold)

		if (header == "description"):

			val = QTextEdit(column_val)
			val.textChanged.connect(description_changed)
			my_widget.description_editor = val

		elif ( header == "filename" ):
			val = QLabel(column_val)
			my_widget.display_filename_field = val
			
		else:
			val = QLineEdit(column_val);

			if (header == "title"):
				val.textChanged.connect(title_changed)
				my_widget.display_title_field = val

			elif (header == "year"):
				val.textChanged.connect(year_changed)
				my_widget.display_year_field = val

			elif (header == "season"):
				val.textChanged.connect(season_changed)
				my_widget.display_season_field = val

			elif (header == "episode"):
				val.textChanged.connect(episode_changed)
				my_widget.display_episode_field = val

			elif (header == "genre"):
				val.textChanged.connect(genre_changed)
				my_widget.display_genre_field = val

		grid.addWidget(label, row_index, 0)
		grid.addWidget(val, row_index, 1)

		row_index = row_index + 1

	crews_label = QLabel("Crews")
	crews_label.setFont(bold)

	grid.addWidget(crews_label, row_index, 0, 1, 2)
	grid.setAlignment(crews_label, Qt.AlignHCenter)

	row_index = row_index + 1

	#Crews Table
	crews = read_entire_crew(movie_id)

	my_widget.crews = crews

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

	grid.addWidget(crews_table, row_index, 0, 1, 2)

	my_widget.crews_table = crews_table

	scroll = QScrollArea()
	scroll.setWidget(display_widget)

	main_window.setCentralWidget(scroll)

'''Clicked a row in the crews table'''
def crews_row_clicked(row, col):
	
	crews_table = my_widget.crews_table

	clicked_item = crews_table.item(row, 1)

	if (clicked_item != None):

		name = clicked_item.text()	
		display_crew(my_widget.current_movie, name)

'''Display the cast member'''
def display_crew(movie_id, name):

	selected_crew = None

	crews = my_widget.crews

	for crew_id in crews:
		if ( crews[crew_id]["name"] == name ):
			selected_crew = crew_id

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
		grid.setAlignment(poster_label, Qt.AlignVCenter)


		#name
		name_label = QLabel("<b>Name:</b>" + crews[selected_crew]["name"])

		grid.addWidget(name_label,1, 0)
		grid.setAlignment(name_label, Qt.AlignVCenter)

		bio_label = QLabel("Biography")

		grid.addWidget(bio_label,2, 0)
		grid.setAlignment(bio_label, Qt.AlignVCenter)

		bio_str = "<p>" + crews[selected_crew]["biography"]

		bio_str = bio_str.replace("Date of Birth", "<b>Date of Birth: </b>", 1)
		bio_str = bio_str.replace("Height", "<b>Height: </b>", 1)

		bio_str = bio_str.replace("\n", "<p>")
		bio_field = QTextEdit(bio_str)

		grid.addWidget(bio_field,2, 0)
		grid.setAlignment(bio_field, Qt.AlignVCenter)
	
		widget = QWidget()
		widget.setLayout(grid)

		main_window.setCentralWidget(widget)
		
	
'''Go back in the menu'''
def back():
	load_catalogue(my_widget.main_window, None)

	
def load_toolbar(main_window):

	#Go Back
	backAction = QAction(QIcon('back-icon.png'), 'Back', main_window)
	backAction.setStatusTip('Go Back')
	backAction.triggered.connect(back)

	main_window.toolbar = main_window.addToolBar('Back')
	main_window.toolbar.addAction(backAction)


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
	scanAction = QAction(QIcon('scan-icon.png'), 'Search', main_window)	
	scanAction.setStatusTip('Scan filesystem for movies')
	scanAction.triggered.connect(scan)
        
	main_window.toolbar = main_window.addToolBar('Scan')
	main_window.toolbar.addAction(scanAction)

	my_widget.runs = my_widget.runs + 1

if __name__ == '__main__':

	runs = 0;
    
	app = QApplication(sys.argv)

	main_window = QMainWindow()	
 
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

