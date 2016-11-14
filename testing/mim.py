#!/bin/env python

import sys

import imobiledevice
from imobiledevice import *

from plist import Dict

from time import sleep

reload(sys)

sys.setdefaultencoding("UTF8")

def get_lockdown():
	while True:
		try:
			ld = LockdownClient(iDevice())
			
			return ld
		except iDeviceError:
			continue
		except LockdownError:
			continue

def get_client(service_class, ld=None):
	if ld == None:
		ld = get_lockdown()
	
	return ld.get_service_client(service_class)

def get_afc(ld=None):
	if ld == None:
		ld = get_lockdown()
	
	return get_client(AfcClient, ld)

def get_mim(ld=None):
	if ld == None:
		ld = get_lockdown()
	
	return get_client(MobileImageMounterClient, ld)

def upload(source, dest, afc=None):
	if afc == None:
		afc = get_afc()
	
	try:
		with open(source, "r") as local_file:
			with afc.open(dest, mode="w") as remote_file:
				data = local_file.read()
				
				remote_file.write(data)
	except Exception, e:
		print(e)

public_staging = "/PublicStaging/"

dmg_name = "DeveloperDiskImage.dmg"
signature_name = "DeveloperDiskImage.dmg.signature"

dmg_dest = public_staging + "staging.dimage"

ld = get_lockdown()

afc = get_afc(ld)
mim = get_mim(ld)

upload(dmg_name, dmg_dest)

print("== Current mount status ==")

print(mim.lookup_image("Developer"))

print("== Building mount PLIST ==")
mount_plist = Dict()

mount_plist["Command"] = "MountImage"
mount_plist["ImageType"] = "Developer"

mount_plist["ImagePath"] = "/var/mobile/Media/PublicStaging/staging.dimage"

with open(signature_name, "rb") as sig:
	signature = sig.read()

print(" - Signature:")
print(signature)

mount_plist["ImageSignature"] = sig

mim.send(mount_plist)

sleep(5)

result = mim.lookup_image("Developer")

for entry in result:
	value = result[entry]
		
	print(entry + ": " + str(value))
