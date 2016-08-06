from imobiledevice import *

ld = LockdownClient(iDevice())

afc = ld.get_service_client(AfcClient)

while True:
	contents = afc.read_directory("PublicStaging")
	
	print(contents)
