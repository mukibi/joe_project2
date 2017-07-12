from __future__ import print_function

import numpy as np
import cv2

import os.path
import sys

import subprocess

import re
import shlex

import sqlite3

import os

#the filename to process is passed in as 
#the 1st commandline arg
if (len(sys.argv) > 1):
	file_name = sys.argv[1]
	remove_ads(file_name)

'''Remove ads from file f_name'''
def remove_ads(f_name):

	if (not os.path.exists(f_name)):
		return 0

	f_name_ext = ""

	dot = f_name.rfind(".")
	if (dot != -1):
		f_name_ext = f_name[dot:]


	#initialize ad_remover_percent and ad_remover_file
	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("DELETE FROM configuration WHERE key='ad_remover_complete' OR key='ad_remover_file' OR key='ad_remover_stage' OR key='ads_seen'")
	cursor.execute("INSERT INTO configuration VALUES ('ad_remover_complete', '0'), ('ad_remover_stage', '0'), ('ad_remover_file', ?), ('ads_seen', '0')", (f_name,))

	connection.commit()
	connection.close()
	
	cap = cv2.VideoCapture(f_name)

	fps_line_re = re.compile("^\s*Stream #0:0:.*?(\d+) fps,")
	duration_line_re = re.compile("^\s*Duration: (\d+):(\d+):(\d+)\.(\d+),")

	#expects ads of len 10s-60s
	min_ad_len_secs = 10
	max_ad_len_secs = 60

	fps = 30
	duration_secs = 0

	#get fps and video duration using ffmpeg
	try:

		args = shlex.split("ffmpeg -i %s" % f_name)
		pipe = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		ffprobe_output  = pipe.communicate()[1]

		ffprobe_output_lines = ffprobe_output.split("\n")

		cntr = 0

		for line in ffprobe_output_lines:
			cntr = cntr + 1

			matched_fps = re.match(fps_line_re, line)
			if (matched_fps):
				fps = matched_fps.group(1)	

			else:

				matched_duration = re.match(duration_line_re, line)

				if (matched_duration):

					hrs  = matched_duration.group(1)
					mins = matched_duration.group(2)
					secs = matched_duration.group(3)
					centi_secs = matched_duration.group(4)

					secs = float(secs)

					secs += (int(mins) * 60)
					secs += (int(hrs) * 60 * 60)

					secs += (float(centi_secs) / 100)

					duration_secs = secs

	except subprocess.CalledProcessError:
		pass

	min_ad_len_frames = 10 * fps
	max_ad_len_frames = 60 * fps
  
	frame_cntr = 0
	num_consecutive_blanks = 0

	in_ad = False
	valid_ad = False

	non_ad_segments = []
	segment_start = 0

	ad_start = 0

	last_percent = 0

	while(True):
 
		ret, frame = cap.read()

		if (not ret):
			break

		# Our operations on the frame come here
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		height, width = gray.shape
		num_pixels = height * width * 0.99
	
		#calculate histogram
		hist = cv2.calcHist([gray],[0],None,[256],[0,256])

		#check if blank i.e 99% of pixels are of the same color

		blank = False

		for pix_val in hist:
			if (pix_val[0] >= num_pixels):
				blank = True
				break

		if ( blank ):

			#closing ad
			if (in_ad):

				intervening_frames = frame_cntr - ad_start
				#check if within min_ad_len_frames and max_ad_len_frames
				if ( intervening_frames >= min_ad_len_frames and intervening_frames <= max_ad_len_frames ):
					valid_ad = True

				#in_ad = False

			#open ad
			else:
				num_consecutive_blanks = num_consecutive_blanks + 1
				#seen 10 consecutive frames
				if ( num_consecutive_blanks >= 10 ):
					in_ad = True

					segment_stop = frame_cntr - num_consecutive_blanks;
					ad_start = frame_cntr

		else:
			#close ad
			if (in_ad):

				if ( valid_ad ):

					start_stop_tuple = tuple([segment_start/fps, segment_stop / fps])
					#append segment
					non_ad_segments.append(start_stop_tuple)

					#next segments starts here
					segment_start = frame_cntr

					#increment ads_seen
					connection = sqlite3.connect("movie_catalogue.db")
					cursor = connection.cursor()

					cursor.execute("UPDATE configuration SET VALUE=value+1 WHERE key='ads_seen'")

					connection.commit()
					connection.close()

				in_ad = False

			num_consecutive_blanks = 0

	
		#update after processing 1% more 
		frame_cntr = frame_cntr + 1
		
		secs_processed = float(frame_cntr / fps)
		percent_complete = round(secs_processed / duration_secs)

		if ( (percent_complete - last_percent) > 1):

			#update ad_remover_percent
			connection = sqlite3.connect("movie_catalogue.db")
			cursor = connection.cursor()

			cursor.execute("UPDATE configuration SET VALUE=? WHERE key='ad_remover_complete'", (percent_complete,) )

			connection.commit()
			connection.close()

			last_percent = percent_complete

		#if ( frame_cntr > 2000 ):
		#	break

		# Display the resulting frame
		#cv2.imshow('frame',frame)
		#cv2.waitKey(100)

	#clip movie
	#update ad_remover_stage
	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("UPDATE configuration SET VALUE=1 WHERE key='ad_remover_stage'")

	connection.commit()
	connection.close()


	for ad_segment in (range(0, len(non_ad_segments))):

		start = non_ad_segments[ad_segment][0]
		stop  = non_ad_segments[ad_segment][1]

		#delete segment incase it already exists
		seg_name = str(ad_segment) + f_name_ext
		if ( os.path.exists(seg_name) ):
			os.remove(str(ad_segment) + f_name_ext)

		#call ffmpeg
		command_str = "ffmpeg -i '%s' -ss %d -to %d -c copy %s" % (f_name, start, stop, str(ad_segment) + f_name_ext)
		args = shlex.split(command_str)
		subprocess.call(args)

	#last segment
	#segment start should hold the
	#start of the last non-ad segment 
	#seen
	if ( os.path.exists("last" + f_name_ext) ):
		os.remove("last" + f_name_ext)

	command_str = "ffmpeg -i '%s' -ss %d -c copy %s" % (f_name, segment_start, "last" + f_name_ext)
	args = shlex.split(command_str)
	subprocess.call(args)

	#create list of concat files
	with open("concat.txt", "w") as out:
		for ad_segment in (range(0, len(non_ad_segments))):
			seg_name = str(ad_segment) + f_name_ext
			if ( os.path.exists(seg_name) ):
				out.write("file %s\n" % (seg_name))

		if (os.path.exists("last" + f_name_ext)):
			out.write("file %s\n" % ("last" + f_name_ext))	

	#call concat
	#remove old f_name to avoid over-write warning
	os.remove(f_name)

	command_str = "ffmpeg -f concat -i concat.txt -c copy '%s'" % (f_name)
	args = shlex.split(command_str)
	subprocess.call(args)

	#delete segments
	for ad_segment in (range(0, len(non_ad_segments))):
		seg_name = str(ad_segment) + f_name_ext
		if ( os.path.exists(seg_name) ):
			os.remove(seg_name)

	if ( os.path.exists("last" + f_name_ext) ):
		os.remove("last" + f_name_ext)


	#delete concat.txt
	if ( os.path.exists("concat.txt") ):
		os.remove("concat.txt")

	#update ad_remover_stage
	connection = sqlite3.connect("movie_catalogue.db")
	cursor = connection.cursor()

	cursor.execute("UPDATE configuration SET VALUE=2 WHERE key='ad_remover_stage'")

	connection.commit()
	connection.close()


	# When everything done, release the capture
	cap.release()
	#cv2.destroyAllWindows()

