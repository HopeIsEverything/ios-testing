#import <Foundation/Foundation.h>

#define LC_SOURCE_VERSION 1.0.0

__attribute__((constructor))
static void initializer()
{
	NSLog(@"I loaded. :)");
}
