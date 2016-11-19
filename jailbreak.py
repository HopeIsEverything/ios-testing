#!/usr/bin/python

from __future__ import print_function

import sys, os
import imobiledevice
from imobiledevice import *
import libarchive
from subprocess import call
from zipfile import ZipFile
import plist, plistlib
from time import sleep
import tempfile
import shutil

current_dir = os.getcwd()

tmp_dir = tempfile.mkdtemp()
print(tmp_dir)
os.chdir(tmp_dir)

def get_lockdown():
	while True:
		try:
			ld = LockdownClient(iDevice())
			return ld
		except iDeviceError:
			continue
		except LockdownError:
			continue

def get_client(service_class):
        ld = get_lockdown()
        return ld.get_service_client(service_class)

def get_afc():
	return get_client(AfcClient)

def get_fr():
	return get_client(FileRelayClient)

def get_drr():
	return get_client(DiagnosticsRelayClient)

def get_ip():
	return get_client(InstallationProxyClient)

ld = get_lockdown()

afc = get_afc()
fr = get_fr()
drr = get_drr()
ip = get_ip()

descriptor = None
port = 0

afc_unrestricted = None

def upload_recursively(folder, destination):
	for x in os.walk(folder):
		afc.make_directory(destination + "/" + x[0])
	
		for file in x[2]:
			with afc.open(destination + "/" + x[0] + "/" + file, "w") as rfile:
				with open(x[0] + "/" + file, "r+") as lfile:
					data = lfile.read()
					rfile.write(data)

def upload_app_stage_1():
	print("== Uploading Juniper app (1/2) ==")
	
	print(" - Extracting IPA")
	
	shutil.copyfile(os.path.join(current_dir, "resources", "jailbreak.ipa"), "jailbreak.ipa")
	
	with ZipFile("jailbreak.ipa", "r") as ipa:
		ipa.extractall(tmp_dir)
	
	print(" - Uploading app")
	
	os.chdir("Payload")
	
	upload_recursively("Jailbreaker.app", "Downloads")

def upload_app_stage_3(order, message):
	try:
		if message.get("Status").get_value() != "Complete":
			return
	except AttributeError:
		return
	
	afc = get_afc()
	
	print("== Uploading Juniper app (3/3) ==")
	print(" - Modifying files")
	
	os.chdir(current_dir)
	with afc.open("Downloads/sandbox.dylib", "w+") as sandbox, open("resources/codesign/sandbox.dylib", "r") as sandbox_local:
		sandbox.write(sandbox_local.read())
	os.chdir(tmp_dir)
	
	configure_system_stage_1()
	configure_system_stage_2()
	own_block_device()
	modify_root_filesystem()

def upload_app_stage_2():
	print("== Uploading Juniper app (2/3) ==")
	print(" - Modifying Info.plist")
	
	os.chdir("Jailbreaker.app")
	
	call(["plistutil", "-i", "Info.plist", "-o", "Info.plist.tmp"])
	
	file_contents = ""
	next_is_executable = False
	
	with open("Info.plist.tmp", "r") as info:
		for line in info:
			if next_is_executable and line.find("..") == -1:
				file_contents += line.replace("Jailbreaker", "../../../../../../var/mobile/Media/Downloads/Jailbreaker.app/Jailbreaker")
				next_is_executable = False
			elif next_is_executable:
				next_is_executable = False
			else:
				if line.find("CFBundleExecutable") != -1:
					next_is_executable = True
				file_contents += line
	
	with open("Info.plist.tmp", "w") as info:
		info.write(file_contents)
	
	call(["plistutil", "-i", "Info.plist.tmp", "-o", "Info.plist"])
	
	os.remove("Info.plist.tmp")
	
	os.chdir(tmp_dir)
	
	print(" - Packaging Juniper app")
	
	with ZipFile("jailbreak_modified.ipa", "w") as repackaged_app:
		repackaged_app.write("iTunesArtwork")
		repackaged_app.write("iTunesMetadata.plist")
		
		for x in os.walk("Payload"):
			for child in x[2]:
				repackaged_app.write(x[0] + "/" + child)
	
	print(" - Installing Juniper app")
	
	afc.make_directory("/PublicStaging")
	
	with afc.open("/PublicStaging/jailbreak.ipa", "w") as remote_app:
		with open("jailbreak_modified.ipa", "r") as local_app:
			remote_app.write(local_app.read())
		
	install_dict = plist.from_xml("<plist><dict><key>CFBundleIdentifier</key><string>com.trinitigame.jailbreakerfull</string></dict></plist>")
	ip.install("/PublicStaging/jailbreak.ipa", install_dict, upload_app_stage_3)
	
	print(" - Please wait for the app to install...")
	
	while True:
		sleep(0.1)

def configure_system_stage_1(): 
	print("== Configuring system (1/2) ==")
	print(" - Working AFC magic")
	
	afc.make_directory("Downloads/a")
	afc.make_directory("Downloads/a/a")
	afc.make_directory("Downloads/a/a/a")
	afc.make_directory("Downloads/a/a/a/a")
	afc.make_directory("Downloads/a/a/a/a/a")
	
	afc.symlink("../../../../../tmp", "Downloads/a/a/a/a/a/link")
	afc.rename_path("Downloads/a/a/a/a/a/link", "tmp")

def log_args(order, message):
	print("Order: " + str(order))
	print("Message: " + str(message))

def race_installd(zip_file, destination):
	ip = get_ip()
	
	try:
		while True:
			with afc.open("/PublicStaging/" + zip_file, "w") as remote:
				with open(zip_file, "r") as local:
					remote.write(local.read())
			
			options = plist.from_xml("<plist><dict><key>CFBundleIdentifier</key><string>juniper.installd.race</string></dict></plist>")
			
			try:
				ip.install("/PublicStaging/" + zip_file, options)
			except:
				pass
			
			while True:
				try:
					tmp_contents = afc.read_directory("/tmp")
					matching_entries = [i for i in tmp_contents if i.find("install_staging.") != -1]
					
					if len(matching_entries) is 0:
						continue
					
					entry = matching_entries[0]
					
					staging_contents = afc.read_directory("/tmp/" + entry)
					print
					
					if len(staging_contents) is 2:
						print(" - Succeeded before extraction!")
						afc.symlink("../../../" + destination, "/tmp/" + entry + "/foo_extracted")
						raise StopIteration
					else:
						foo_contents = afc.read_directory("/tmp/" + entry + "/foo_extracted")
						
						if len(foo_contents) is 2:
							print(" - Succeeded during extraction!")
							afc.rename_path("/tmp/" + entry + "/foo_extracted", "/tmp/" + entry + "/foo_extracted.old")
							afc.symlink("../../../" + destination, "/tmp/" + entry + "/foo_extracted")
							raise StopIteration
				except AfcError, e:
					break
	except StopIteration:
		return True

def configure_system_stage_2():
	print("== Configuring system (2/2) ==")
	print(" - Requesting cache")
	
	os.chdir(tmp_dir)
	
	conn = fr.request_sources(["Caches"])
	
	data_length = 0
	
	with open("caches.cpio.gz", "wb+") as dumpfile:
		while True:
			try:
				data = conn.receive_timeout(4096, 10)
				dumpfile.write(data)
				
				data_length += 4096
			except Exception, e:
				if e.code == -2:
					break
				raise e
			
			print(" - " + str(data_length) + " bytes received!", end="\r")
	
	try:
		libarchive.extract.extract_file("caches.cpio.gz")
		libarchive.extract.extract_file("caches.cpio")
	except:
		pass
	
	# The huge space here is to wipe the updating line.
	print(" - Got the cache!           ")
	
	os.chdir("var/mobile/Library/Caches")
	
	call(["plistutil", "-i", "com.apple.mobile.installation.plist", "-o", "com.apple.mobile.installation.plist.tmp"])
	
	file_contents = ""
	
	next_instance = False
	no_more = False
	
	with open("com.apple.mobile.installation.plist.tmp", "r") as install_cache:
		for line in install_cache:
			file_contents += line
	
			if line.find("com.trinitigame.jailbreakerfull") != -1 and not no_more:
				next_instance = True
			
			if next_instance and line.find("/tmp") is not -1:
				file_contents += "\t\t\t\t<key>DYLD_INSERT_LIBRARIES</key>\n"
				file_contents += "\t\t\t\t<string>/var/mobile/Media/Downloads/sandbox.dylib</string>\n"
				
				next_instance = False
				
				no_more = True
	
	with open("com.apple.mobile.installation.plist", "w") as install_cache:
		install_cache.write(file_contents)
	
	os.remove("com.apple.mobile.installation.plist.tmp")
	
	
	
	with open("com.apple.LaunchServices-045.csstore", "w") as launch_services:
		launch_services.write("")
	
	os.chdir(tmp_dir)
	
	ld = get_lockdown()
	
	ios_version = ld.get_value(None, "BuildVersion").get_value()
	
	with open("com.apple.backboardd.plist", "w") as backboardd:
		backboardd.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
		backboardd.write("<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n")
		backboardd.write("<plist version=\"1.0\">\n")
		backboardd.write("<dict>\n")
		backboardd.write("\t<key>BKDataMigratorLastSystemVersion</key>\n")
		backboardd.write("\t<string>" + ios_version + "</string>\n")
		backboardd.write("\t<key>BKNoWatchdogs</key>\n")
		backboardd.write("\t<string>Yes</string>\n")
		backboardd.write("\t<key>InvertColorsEnabled</key>\n")
		backboardd.write("\t<false />\n")
		backboardd.write("</dict>\n")
		backboardd.write("</plist>")
	
	with ZipFile("caches.zip", "w") as caches:
		os.chdir("var/mobile/Library/Caches")
		caches.write("com.apple.mobile.installation.plist")
		caches.write("com.apple.LaunchServices-045.csstore")
		os.chdir(tmp_dir)
	
	with ZipFile("preferences.zip", "w") as preferences:
		preferences.write("com.apple.backboardd.plist")
	
	print(" - Attempting to race installd (caches)")
	
	if race_installd("caches.zip", "/var/mobile/Library/Caches/") != 1:
		print("== Something went wrong, exiting ==")
		
		sys.exit(1)
	
	print(" - Attempting to race installd (preferences)")
	
	if race_installd("preferences.zip", "/var/mobile/Library/Preferences/") != 1:
		print("== Something went wrong, exiting ==")
		
		sys.exit(1)
	
	print(" - Rebooting, please click on the Juniper app when I say so!")
	
	drr.restart(0)

def get_unrestricted_afc():
	ld = get_lockdown()
	
	port = 0
	
	while True:
		try:
			descriptor = ld.start_service(AfcClient)
			port = descriptor.port
		except:
			break
	
	afc = get_afc()
	
	with afc.open("/Downloads/Jailbreaker.app/Jailbreaker", mode="w") as executable:
		executable.write("#!/usr/libexec/afcd -S -d / -p " + str(port) + " # -- ")
	
	print(" - Port: " + str(port))
	
	print("== Alright, click on the icon! ==")
	
	while True:
		try:
			afc_unrestricted = AfcClient(iDevice(), descriptor)
			
			return afc_unrestricted
		except:
			pass

def own_block_device():
	print(" - Waiting for reboot...")
	
	ld = get_lockdown()
	
	afc = get_afc() #ld.get_service_client(AfcClient)
	drr = get_drr()
	
	afc_unrestricted = get_unrestricted_afc()
	
	log_listing = afc_unrestricted.read_directory("/var/mobile/Library/Logs")
	
	if "AppleSupport_moved" not in log_listing:
		afc_unrestricted.rename_path("/var/mobile/Library/Logs/AppleSupport", "/var/mobile/Library/Logs/AppleSupport_moved")
		
		afc_unrestricted.symlink("../../../../../dev/rdisk0s1s1", "/var/mobile/Library/Logs/AppleSupport")
	
	print(" - Rebooting, please click on the icon again when I say so!")
	
	drr.restart(0)

def modify_root_filesystem():
	ld = get_lockdown()
	
	afc = get_afc()
	drr = get_drr()
	
	afc_unrestricted = get_unrestricted_afc()
	
	afc_unrestricted.remove_path("/var/mobile/Library/Logs/AppleSupport")
	afc_unrestricted.rename_path("/var/mobile/Library/Logs/AppleSupport_moved", "/var/mobile/Library/Logs/AppleSupport")
	
	print(" - Moved directories back")
	
	try:
		with afc_unrestricted.open("/dev/rdisk0s1s1", "r") as block:
			with open(os.path.join(tmp_dir, "block")) as local_block:
				block_info = afc_unrestricted.get_file_info("/dev/rdisk0s1s1")
				
				if block_info[0] == "st_size":
					block_size = block_info[1]
				else:
					print("What the fuck")
					return
				
				with tqdm(total = block_size) as pbar:
					chunk = block.read(32768)
					
					if not chunk:
						raise StopIteration
					
					local_block.write(chunk)
					
					pbar.update(32768)
	except StopIteration:
		print("We successfully transferred the block device!")

upload_app_stage_1()
upload_app_stage_2()
upload_app_stage_3()
