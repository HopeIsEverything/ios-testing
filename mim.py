#!/bin/env python

import imobiledevice
from imobiledevice import *

def get_service_client(service):
    ld = LockdownClient(iDevice())
    return ld.get_service_client(service)

mim = get_service_client(MobileImageMounterClient)
mim.mount_image("/PublicStaging/DeveloperDiskImage.dmg", "/PublicStaging/DeveloperDiskImage.dmg", "Developer")
