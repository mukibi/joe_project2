import urllib.request
import urllib.parse

import re

from os.path import basename,splitext,join
from db_utilities import *

import os

import json

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

def omdb_search(movie_id, title, year=None, season=None, episode=None, search_genre=None):

	if (title == None):
		return

	quoted_title = urllib.parse.quote(title)

	url = "http://www.omdbapi.com/?s=" + quoted_title

	if ( year != None and year != ""):
		url += "&y=" + urllib.parse.quote(year)

	url += "&plot=full"

	series = False

	if ( season != None and season != "" and episode != None and episode != "" ):
		url += "&type=series"
		series = True

	else:
		url += "&type=movie"

	response = ""

	try:
		with urllib.request.urlopen(url) as f:
			for line in f.readlines():
				response += line.decode("utf-8")

	except urllib.request.URLError:
		return
	except UnicodeEncodeError:
		return

	if (len(response) == 0):
		return

	data = json.loads(response)

	imdb_id = None
	saved_title = title

	try:
		search_results = data["Search"]		
		
		print(search_results)

		#search by genre
		selected_index = 0
	
		#print("Chose:", selected_index)

		selection = search_results[selected_index]
		#print(selection)
		#selection = search_results[0]

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
				return
			except UnicodeEncodeError:
				return
	
			selection = json.loads(response)

			print(selection)

			saved_title = selection["Title"]
			#update_catalogue(movie_id, "title", saved_title)

			yr = selection["Year"]
			#update_catalogue(movie_id, "year", yr)

			genre = selection["Genre"]
			genres = ",".split(genre)

			#update_catalogue(movie_id, "genre", genres[0])

			#get poster
			poster_url = selection["Poster"]

			print(poster_url)

			if ( re.match("^https?://", poster_url, re.IGNORECASE) ):

				extension = ""
				ext_index = poster_url.rfind(".")

				if (ext_index >= 0):
					extension = poster_url[poster_url.rfind("."):]

				out_file_dir = read_conf("pictures_directory")
				out_file_dir = join(out_file_dir, "full")

				out_file = join(out_file_dir, movie_id + extension)

				pic_file = open(out_file, "w+b")

				try:
					with urllib.request.urlopen(poster_url) as f:
						for line in f:
							pic_file.write(line)

					
					#update_catalogue(movie_id, "cover_picture", out_file)
				except URLError:
					pass

			description = selection["Plot"]
			#update_catalogue(movie_id, "description", description)
		
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

			#update_crew(movie_id, all_crew)

		except KeyError:
			pass

	except KeyError:
		pass

omdb_search("1", "i am wrath")
