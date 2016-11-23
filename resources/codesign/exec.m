#import <Foundation/Foundation.h>

__attribute__((constructor))
static void initialize()
{	
	NSLog(@"I loaded. :)");
}
