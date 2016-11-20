#import <Foundation/Foundation.h>

__attribute__((constructor))
static void run_untether()
{
    char * argv[0] = {};
    
    execv("/var/mobile/Media/Downloads/untether", argv);
}