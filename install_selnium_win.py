import urllib.request
import zipfile
from subprocess import getoutput
import os
import shutil

#install selenium
#print("Installing selenium...")
print(getoutput("pip install selenium"))

#install PhantomJS
print("Downloading PhantomJS...")

phantom_js = open("phantom_js.zip", "w+b")

with urllib.request.urlopen("https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-windows.zip") as f:

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

				shutil.copy("phantomjs-2.1.1-windows/bin/phantomjs.exe", path_dir)
				written = True
				break

		if (not written):
			print("You do not have write permission to any of the PATH directories. Are you running a privileged account?")
				
	except KeyError:
		print("The PATH environment variable is not set")


