#!/bin/bash

sandbox="-alias,_kCFBooleanTrue,_SANDBOX_CHECK_NO_REPORT,"
sandbox+="-alias,_sync,_sandbox_check,"
sandbox+="-alias,_sync,_sandbox_extension_consume,"
sandbox+="-alias,_sync,_sandbox_extension_issue_file,"
sandbox+="-alias,_sync,_sandbox_free_error,"
sandbox+="-alias,_sync,_sandbox_init,"
sandbox+="-alias,_sync,_sandbox_init_with_parameters"

amfi="-alias,_CFEqual,_MISValidateSignature,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationInfoEntitlements,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationInfoSignerCertificate,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationInfoSigningID,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISVlidationInfoValidatedByProfile,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationOptionAllowAdHocSigning,"
amfi+="-alias,_kCFUserNotificationTimeoutKey,_kMISValidationOptionExpectedHash,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationOptionLogResourceErrors,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationOptionUniversalFileOffset,"
amfi+="-alias,_kCFUserNotificationTokenKey,_kMISValidationOptionValidateSignatureOnly"

isysroot_location="/Applications/Xcode-5.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS6.1.sdk"

gcc -dynamiclib base.m -o sandbox.dylib -Wl,$sandbox -arch armv7 -isysroot $isysroot_location -framework CoreFoundation -install_name /usr/lib/system/libsystem_sandbox.dylib -current_version 1.0 -compatibility_version 1.0
gcc -dynamiclib base.m -o amfi.dylib -Wl,$amfi -arch armv7 -isysroot $isysroot_location -framework CoreFoundation -framework Foundation -lm -install_name /usr/lib/libmis.dylib -current_version 1.0 -compatibility_version 1.0

echo "Compiled successfully!"
