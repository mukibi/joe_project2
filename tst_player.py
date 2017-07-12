from db_utilities import *
import subprocess

player = read_conf("player")
	
if ( player != None ):

	filename = None

	catalogue = read_entire_catalogue(None)

	for entry in catalogue:

		if (catalogue[entry]["filename"] != None):

			filename = catalogue[entry]["filename"]	
			break

	if (filename != None):
		print(subprocess.getoutput('%s "%s"' % (player, filename)))
	else:
		print("Could not retrieve any movie from the catalogue. Is the catalogue empty?")

else:
	print("Player not configured")

