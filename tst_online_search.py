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

					except KeyError:
						pass
		
		print("Chose:", selected_index)

		selection = search_results[selected_index]
		print(selection)
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

			saved_title = selection["Title"]
			#update_catalogue(movie_id, "title", saved_title)

			yr = selection["Year"]
			#update_catalogue(movie_id, "year", yr)

			genre = selection["Genre"]
			genres = ",".split(genre)

			#update_catalogue(movie_id, "genre", genres[0])

			#get poster
			poster_url = selection["Poster"]

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

	driver = None
	
	if (imdb_id != None):
		driver = webdriver.PhantomJS(service_args=["--load-images=no"])

	if ( series and imdb_id != None ):

		#read imdb.com for list of episodes
		response = ""

		seasons_url = "http://www.imdb.com/title/%s/episodes?season=%s" % (imdb_id, season);	

		driver.get(seasons_url);

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
					#update_catalogue(movie_id, "title", new_title)
					cntr = cntr + 1

				else:
					description += line + ". "
			
		if ( description != "" ):
			#update_catalogue(movie_id, "description", description)
			pass

	#full cast

	if ( imdb_id != None ):


		seasons_url = "http://www.imdb.com/title/%s/fullcredits" % (imdb_id,);

		#print(seasons_url)

		driver.get(seasons_url);
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

						if ( cast_cntr > 0 ):
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
		
		#update_cast
		print(cast)

		#update_cast(movie_id, cast)

omdb_search("1", "Ben Hur", search_genre="jk)

