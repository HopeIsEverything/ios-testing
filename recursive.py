import os
import imobiledevice
from imobiledevice import *

ld = LockdownClient(iDevice())
afc = ld.get_service_client(AfcClient)

def recurse(folder, destination):
	for x in os.walk(folder):
		afc.make_directory(destination + "/" + x[0])

		for file in x[2]:
			with afc.open(destination + "/" + x[0] + "/" + file, "w+") as rfile:
				local_file = open(x[0] + "/" + file, "r+")
				rfile.write(local_file.read())

recurse("Payload", "/Downloads")
