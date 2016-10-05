from imobiledevice import *
import random
from time import sleep

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

def is_dir(afc, path):
	info = afc.get_file_info(path)
	
	if info[7] == "S_IFDIR":
		return True
	else:
		return False

def get_file_children(afc, path):
	if not is_dir(afc, path):
		raise ValueError
	
	children = afc.read_directory(path)
	file_children = []
	
	if path[-1] == "/" and path != "/":
		path = path[:-1]
	
	for child in children:
		if child == "." or child == "..":
			continue
		
		if not is_dir(afc, path + "/" + child):
			if path == "/":
				file_children.append("/" + child)
			else:
				file_children.append(path + "/" + child)
	
	return file_children

def get_dir_children(afc, path):
	if not is_dir(afc, path):
		raise ValueError
	
	children = afc.read_directory(path)
	dir_children = []
	
	if path[-1] == "/" and path != "/":
		path = path[:-1]
	
	for child in children:
		if child == "." or child == "..":
			continue
		
		if is_dir(afc, path + "/" + child):
			if path == "/":
				dir_children.append("/" + child)
			else:
				dir_children.append(path + "/" + child)
	
	return dir_children

def walk_directory(afc, path):
	if not is_dir(afc, path):
		raise ValueError
	
	entries = []
	
	file_children = get_file_children(afc, path)
	dir_children = get_dir_children(afc, path)
	
	entries.append((path, file_children, dir_children))
	
	for dir in dir_children:
		entries += walk_directory(afc, dir)
		print(dir)
	
	return entries

afc = get_afc()

contents = walk_directory(afc, "/")

times = 0

while times < 100:
	times += 1
	
	if random.random() > 0.99:
		contents = walk_directory(afc, "/")
	
	entry = random.choice(contents)
	
	link_dest = "../" * random.randint(1, 5)
	link_name = entry[0] + "/link"
	
	print(link_dest + " " + link_name)
	
	if random.randint(1, 2) == 1:
		link_dest = "../" * random.randint(1, 5)
		link_name = entry[0] + "/link"
		
		try:
			afc.symlink(link_dest, link_name)
		except AfcError, e:
			print(e)
			continue
	else:
		entry_two = random.choice(contents)
		
		entry_split = entry_two[0].split("/")
		
		new_loc = entry_two[0]
		
		cut = len(entry_split[-1])
		new_loc = new_loc[:-cut]
		new_loc += entry[0].split("/")[-1]
		
		print(entry[0] + " " + new_loc)
		
		try:
			afc.rename_path(entry[0], new_loc)
		except AfcError, e:
			print(e)
			continue
	
	sleep(0.3)

contents = walk_directory(afc, "/")

for entry in contents:
	for file in entry[1]:
		if file.find("link") != -1:
			try:
				children = afc.read_directory(file)
			except AfcError:
				continue
			
			print(entry[0] + ": " + contents)
