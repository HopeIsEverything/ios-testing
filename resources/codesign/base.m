#import <syslog.h>

#define LC_SOURCE_VERSION 1.0.0

__attribute__((constructor))
static void initializer()
{
	syslog(LOG_NOTICE, "I loaded. :)");
}
