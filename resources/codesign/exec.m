#import <Foundation/Foundation.h>

#define LC_SOURCE_VERSION 1.0.0

static void __attribute__((constructor)) initialize(void)
{
	NSLog(@"I loaded. :)");
}
