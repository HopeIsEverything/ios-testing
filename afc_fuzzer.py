#!/bin/env python

import imobiledevice
from imobiledevice import *
import math, random, sys

files = ["Containers", "Documents", "Library", "Media"]

def add(prefix, path):
    

files += ["Containers/Bundle", "Containers/Bundle/Application", "Containers/Data", "Containers/Shared"]
add("Containers", "Bundle")
add("C
files += ["Library/AddressBook", "Library

while True:
    base = random.choice(files)
    path = base + "/link"
    print("symlink('" + "../" * int(math.floor(random.random() * 10)) + "tmp'" + ", '" + path + "')")

try:
    ld = LockdownClient(iDevice())
    afc = ld.get_service_client(AfcClient)
except iDeviceError:
    print("No iDevice :(")
    sys.exit(1)

# Beyond here is for when I have an iDevice

files = afc.read_directory("/")

while True:
    afc.symlink("../" * math.floor(random.random() * 10) + "tmp", "Downloads/link")

