#!/usr/bin/env python3
"""Exercise the production spawn/cleanup handoff with mocked privilege RPCs.

Uses only temporary local child processes. No device, jailbreak or root access.
"""
from pathlib import Path
import subprocess
import tempfile

application = Path(__file__).resolve().parents[1]
source = (application / "Dopamine/Jailbreak/DOEnvironmentManager.m").read_text()
start = source.index("- (int)spawnJbctlAsRootWithArgs:")
end = source.index("\n- (int)runTrollStoreAction:", start)
method = source[start:end]
preamble = r'''#import <Foundation/Foundation.h>
#include <spawn.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/wait.h>
#include <assert.h>
#include <fcntl.h>
extern char **environ;
static const char *childPath;
static uid_t effectiveUser, expectedUser;
static gid_t effectiveGroup, expectedGroup;
static uint64_t sandboxLabel;
static int failPipe, denyRoot, denySandbox, failRestore, failDrop, dropDoesNothing;
static int lostRootReply, failWrite, interruptWait, spawnCount, writeCount, rootCalls, dropCalls, labelCalls;
static uid_t test_geteuid(void) { return effectiveUser; }
static gid_t test_getegid(void) { return effectiveGroup; }
static int test_pipe(int p[2]) { if(failPipe) {errno=EMFILE;return -1;} return pipe(p); }
static int jbclient_dopamine_get_root(void) {
 ++rootCalls;if(denyRoot)return EPERM;
 effectiveUser=effectiveGroup=0;return lostRootReply?EIO:0;
}
static int jbclient_dopamine_drop_root(void) {
 ++dropCalls;if(failDrop)return EIO;
 if(!dropDoesNothing){effectiveUser=expectedUser;effectiveGroup=expectedGroup;}return 0;
}
static int jbclient_root_set_mac_label(uint64_t slot,uint64_t label,uint64_t *previous) {
 assert(slot==1 && effectiveUser==0);++labelCalls;
 if(previous) {assert(label==UINT64_MAX);if(denySandbox)return EIO;*previous=sandboxLabel;sandboxLabel=label;return 0;}
 assert(label==42);if(failRestore)return EIO;sandboxLabel=label;return 0;
}
static int test_spawn(pid_t *pid,const char *path,const posix_spawn_file_actions_t *actions,
 const posix_spawnattr_t *attr,char *const argv[],char *const envp[]) {
 ++spawnCount;assert(effectiveUser==0 && effectiveGroup==0);
 return posix_spawn(pid,path,actions,attr,argv,envp);
}
static ssize_t test_write(int fd,const void *buffer,size_t length) {
 ++writeCount;
 assert(effectiveUser==expectedUser && effectiveGroup==expectedGroup && sandboxLabel==42);
 assert(!failRestore && !failDrop && !dropDoesNothing);
 if(failWrite){errno=EIO;return -1;}
 return write(fd,buffer,length);
}
static pid_t test_waitpid(pid_t pid,int *status,int flags) {
 assert(pid>0);
 if(interruptWait){interruptWait=0;errno=EINTR;return -1;}
 return waitpid(pid,status,flags);
}
#define geteuid test_geteuid
#define getegid test_getegid
#define pipe test_pipe
#define posix_spawn test_spawn
#define write test_write
#define waitpid test_waitpid
#define JBROOT_PATH(p) childPath
@interface DOEnvironmentManager : NSObject
@property NSString *jailbrokenVersion;
@property BOOL isJailbroken;
@property BOOL isInstalledThroughTrollStore;
- (int)spawnJbctlAsRootWithArgs:(NSArray *)args;
@end
@implementation DOEnvironmentManager
'''
postamble = r'''
@end
static void reset(DOEnvironmentManager *d) {
 effectiveUser=expectedUser=501;effectiveGroup=expectedGroup=501;sandboxLabel=42;
 failPipe=denyRoot=denySandbox=failRestore=failDrop=dropDoesNothing=lostRootReply=failWrite=interruptWait=0;
 spawnCount=writeCount=rootCalls=dropCalls=labelCalls=0;
 d.jailbrokenVersion=@"3.0.10-s4";d.isJailbroken=YES;d.isInstalledThroughTrollStore=NO;
}
static void check(DOEnvironmentManager *d,int expected,int spawns,int writes) {
 int result=[d spawnJbctlAsRootWithArgs:@[@"modern"]];
 assert(result==expected && spawnCount==spawns && writeCount==writes);
}
int main(int argc,char **argv) {@autoreleasepool {
 assert(argc==2);childPath=argv[1];DOEnvironmentManager *d=[DOEnvironmentManager new];
 for(NSString *v in @[@"3.0.5",@"3.0.10",@"3.0.10-s4",@"3.1.0"]){
  reset(d);d.jailbrokenVersion=v;check(d,0,1,1);assert(rootCalls==1 && dropCalls==1 && labelCalls==2);
 }
 reset(d);d.jailbrokenVersion=@"3.0.4";assert([d spawnJbctlAsRootWithArgs:@[@"legacy"]]==0 && writeCount==0);
 reset(d);denyRoot=1;check(d,EPERM,0,0);assert(dropCalls==0 && labelCalls==0);
 reset(d);lostRootReply=1;check(d,EPERM,0,0);assert(dropCalls==1 && effectiveUser==501);
 reset(d);denySandbox=1;check(d,EACCES,0,0);assert(dropCalls==1 && effectiveUser==501);
 reset(d);failRestore=1;check(d,EACCES,1,0);assert(dropCalls==1 && effectiveUser==501);
 reset(d);failDrop=1;check(d,EPERM,1,0);assert(sandboxLabel==42);
 reset(d);dropDoesNothing=1;check(d,EPERM,1,0);
 reset(d);failPipe=1;check(d,EMFILE,0,0);assert(rootCalls==0);
 reset(d);failWrite=1;check(d,EIO,1,1);
 reset(d);interruptWait=1;check(d,0,1,1);
 reset(d);d.isJailbroken=NO;check(d,EPERM,0,0);
 reset(d);d.isInstalledThroughTrollStore=YES;check(d,0,1,1);assert(labelCalls==0);
 reset(d);effectiveUser=expectedUser=0;effectiveGroup=expectedGroup=0;check(d,0,1,1);assert(rootCalls==0 && dropCalls==0);
 reset(d);const char *saved=childPath;childPath="/no/such/jbctl";check(d,ENOENT,1,0);
 assert(sandboxLabel==42 && effectiveUser==501);childPath=saved;
 reset(d);assert([d spawnJbctlAsRootWithArgs:@[@"exit71"]]==71);
 reset(d);assert([d spawnJbctlAsRootWithArgs:@[@"signal"]]==128+SIGTERM);
 puts("PASS: checked privilege acquisition/restoration, cleanup refusal with no token, raw wait-status decoding, versions and spawn/pipe/write errors");
}return 0;}
'''
child = r'''#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <signal.h>
int main(int argc,char **argv) {
 if(!strcmp(argv[1],"legacy"))return argc==2?0:1;
 if(argc!=4 || strcmp(argv[2],"--waitfor") || strcmp(argv[3],"3"))return 2;
 uint32_t token=0;if(read(3,&token,4)!=4 || token!=1)return 3;
 if(!strcmp(argv[1],"exit71"))return 71;
 if(!strcmp(argv[1],"signal"))raise(SIGTERM);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="dopamine-handoff-test-") as directory:
    scratch = Path(directory)
    (scratch / "handoff.m").write_text(preamble + method + postamble)
    (scratch / "child.c").write_text(child)
    subprocess.run(["xcrun", "clang", "-Wall", "-Wextra", "-Werror", str(scratch / "child.c"), "-o", str(scratch / "child")], check=True)
    subprocess.run(["xcrun", "clang", "-fobjc-arc", "-fblocks", "-Wall", "-Wextra", "-Werror", "-framework", "Foundation", str(scratch / "handoff.m"), "-o", str(scratch / "handoff")], check=True)
    subprocess.run([str(scratch / "handoff"), str(scratch / "child")], check=True, timeout=20)
