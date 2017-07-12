#import urllib.request
#import zipfile
#from subprocess import getoutput
import os
import os.path
import stat
#import shutil

try: 

		path = os.environ['PATH']
		os_sep = os.pathsep

		path_dirs = path.split(os_sep)

		written = False

		for path_dir in path_dirs:

			phantom_js = os.path.join(path_dir, "phantomjs")

			if (os.path.exists(phantom_js)):

				stat_res = os.stat(phantom_js)
				os.chmod(phantom_js, stat_res.st_mode | stat.S_IEXEC)
				written = True
				break

		if (not written):
			print("Could not find phantomjs: Is PhantomJS installed?")
				
except KeyError:
	print("The PATH environment variable is not set")
	
		



