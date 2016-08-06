import imobiledevice
from imobiledevice import *
import plist

ld = LockdownClient(iDevice())
drr = ld.get_service_client(DiagnosticsRelayClient)

descriptor = ld.start_service(AfcClient)

port = descriptor.port

print("Going for " + str(port))

drr.restart(0)

while True:
	try:
		ld = LockdownClient(iDevice())
		break
	except:
		pass

print("Rebooted successfully")

current_port = 0

while current_port is not port - 1:
	try:
		current_port = ld.start_service(AfcClient).port
		print("Port: " + str(current_port))
	except:
		pass

print("We reached it!")
