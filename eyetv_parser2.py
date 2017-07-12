import zipfile
from os.path import join,basename,dirname
import shutil
import xml.etree.ElementTree as ET
import os
import re

from db_utilities import *

#valid vide file extension
video_file_extensions = {
".3g2":"3GPP2",
".3gp":"3GPP",
".amv":"AMV video format",
".asf":"Advanced Systems Format (ASF)",
".avi":"AVI",
".drc":"Dirac",

".f4v":"Flash Video (FLV)",
".flv":"Flash Video (FLV)",
".f4p":"Flash Video (FLV)",
".f4a":"F4V",
".f4b":"F4V",

".gif":"GIF",
".gifv":"Video alternative to GIF",
".m4v":"M4V - (file format for videos for iPods and PlayStation Portables developed by Apple)",
".mkv":"Matroska",
".mng":"Multiple-image Network Graphics",

".mov":"QuickTime File Format",
".qt":"QuickTime File Format",

".mp4":"MPEG-4 Part 14 (MP4)",
".m4p":"MPEG-4 Part 14 (MP4)",
".m4v":"MPEG-4 Part 14 (MP4)",

#".mpg":"MPEG-1",
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

#check files with the expected file extensions
#queing the valid ones


def is_movie_file(file_n):

	movie_ext = None

	for file_extension in video_file_extensions:

		ext_len = len(file_extension)
		file_n_tail = file_n[-ext_len:]

		if (file_extension == file_n_tail.lower()):
			movie_ext = file_n_tail
			break

	return movie_ext

'''Reads a .eyetv|.eyetv.zip file and processes
the contents. First it extracts the zipped movie
file and stores it in the configured directory. Next
it tries to process the dBase file for the movie
information. If that fails(or the file is missing,
it attempts to process the .xml file.'''
def process_eyetv_file(filename, movie_id, eyetv_movies_directory, pictures_directory):

	movie_data = {}

	full_size_pictures = join(pictures_directory, "full")
	thumbnail_pictures = join(pictures_directory, "thumbnails")

	picture_filename = "%s.tiff" % (movie_id)

	if zipfile.is_zipfile(filename):

		eyetv_archive = zipfile.ZipFile(filename, "r")
		
		members = eyetv_archive.namelist();

		extracted_xml   = None

		for member in members:

			lc_member = member.lower()

			is_movie = is_movie_file(member)

			#extract the movie file
			if (is_movie != None):
				
				eyetv_archive.extract(member)
				movie_filename = "%s%s" % (movie_id, is_movie)

				dest_filename = join(eyetv_movies_directory, movie_filename)

				shutil.move(member, dest_filename)

				#delete
				dir_n  =  dirname(member)
				#use shutil.rmtree to delete directory tree
				if (dir_n != ""):
					shutil.rmtree(dir_n)

			#extract pictures
			if ( lc_member.find(".thumbnail.tiff") != -1 ):

				#write to thumbnail pictures directory
				eyetv_archive.extract(member)

				dest_filename = join(thumbnail_pictures, picture_filename)
				shutil.move(member, dest_filename)

			else:
				if ( lc_member.find(".tiff") != -1 ):

					#write to full_size pictures directory
					eyetv_archive.extract(member)

					dest_filename = join(full_size_pictures, picture_filename)
					shutil.move(member, dest_filename)

					#update catalogue pictures 
					movie_data["cover_picture"] = dest_filename
	
			#extract XML file
			if (lc_member.find(".eyetvr") != -1):
				eyetv_archive.extract(member)
				extracted_xml = member

		eyetv_archive.close()

		#process XML file
		if (extracted_xml != None):

			title = ""
			description = ""
			release_yr = ""

			expect_title = False
			expect_description = False
			expect_release_yr = False

			f = open(extracted_xml, "r")

			for line in f:

				if (expect_title):

					matched = re.search("<string>(.*)</string>", line)
					if (matched):
						title = matched.group(1)

					expect_title = False

				elif ( line.find("<key>display title</key>") != -1 ):
					expect_title = True
					
				if (expect_description):

					matched = re.search("<string>(.*)</string>", line)
					if (matched):
						description = matched.group(1)

					expect_description = False

				elif ( line.find("<key>description</key>") != -1 ):
					expect_description = True
	
				if (expect_release_yr):

					matched = re.search("<date>([0-9]{4})", line)
					if (matched):
						release_yr = matched.group(1)

					expect_release_yr = False

				elif ( line.find("<key>actual start time</key>") != -1 ):
					expect_release_yr = True

			movie_data["title"] = title
			movie_data["description"] = description
			movie_data["year"] = release_yr

			#delete extracted XML file
			dir_n  =  dirname(extracted_xml)
			#use shutil.rmtree to delete directory tree
			if (dir_n != ""):
				shutil.rmtree(dir_n)
			else:
				#use os.remove to remove individual file
				os.remove(extracted_xml)

	
	return movie_data

