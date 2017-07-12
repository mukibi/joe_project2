import zipfile
import os.path
import shutil

import os
import re

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
".mpg":"MPEG-1",
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


contents = os.listdir()

eyetv_re = re.compile(".*?\.eyetv(\.zip)?$")

file_list = open("file_list.txt", "w")

eyetv_meta = zipfile.ZipFile("eyetv_meta.zip", "w")

for file in contents:

	if ( os.path.isfile(file) ):

		lc_file = file.lower()

		if ( re.match(eyetv_re, lc_file) ):

			if zipfile.is_zipfile(file):

				eyetv_archive = zipfile.ZipFile(file, "r")
		
				members = eyetv_archive.namelist();

				for member in members:

					extracted_file_name = "%s_%s" % (file, member,)

					file_list.write(extracted_file_name + "\n")
					is_movie = is_movie_file(member)

					print(member, ":", is_movie)

					#extract the movie file
					if (is_movie == None):

						eyetv_archive.extract(member)
						shutil.move(member, extracted_file_name)

						eyetv_meta.write(extracted_file_name)
						pass

				eyetv_archive.close()

file_list.close()

eyetv_meta.write("file_list.txt")
eyetv_meta.close()

