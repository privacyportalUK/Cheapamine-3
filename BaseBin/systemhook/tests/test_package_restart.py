#!/usr/bin/env python3
"""Compile actual command routing with host syscall mocks; never exec or reboot."""
from pathlib import Path
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
test = r'''
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <unistd.h>
#include "package_restart.h"
static uid_t uid_value,euid_value;
static int exec_count,open_count,close_count,identity_error,identity_malformed,identity_calls,helper_missing,exec_error,version_open_error,version_read_error;
static mode_t helper_mode,version_mode;
static uid_t helper_owner,version_owner;
static const char *version_value,*machine_value,*build_value;
static bool root_resolves;
static char *const *expected_environment;
static uid_t mock_getuid(void) { return uid_value; }
static uid_t mock_geteuid(void) { return euid_value; }
static char *mock_realpath(const char *p,char *out) {
    assert(!strcmp(p,"/var/jb") || !strcmp(p,"/test/jb"));
    if (!root_resolves) { errno=ENOENT; return NULL; }
    strcpy(out,"/test/jb"); return out;
}
static int mock_sysctl(const char *name,void *out,size_t *size,void *in,size_t len) {
    assert(!in && !len); ++identity_calls;
    if(identity_malformed) { *size=0; return 0; }
    if(identity_error) { errno=EIO; return -1; }
    const char *v=!strcmp(name,"hw.machine") ? machine_value : build_value;
    assert(*size>strlen(v)); memcpy(out,v,strlen(v)+1); *size=strlen(v)+1; return 0;
}
static int mock_lstat(const char *path,struct stat *st) {
    assert(!strcmp(path,"/test/jb/basebin/jbctl"));
    if(helper_missing) { errno=ENOENT; return -1; }
    memset(st,0,sizeof(*st)); st->st_mode=helper_mode; st->st_uid=helper_owner; return 0;
}
static int mock_open(const char *path,int flags,...) {
    assert(!strcmp(path,"/test/jb/basebin/.version"));
    assert((flags & (O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC))==(O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC)); ++open_count; if(version_open_error) { errno=ELOOP; return -1; } return 44;
}
static int mock_fstat(int fd,struct stat *st) {
    assert(fd==44); memset(st,0,sizeof(*st)); st->st_mode=version_mode; st->st_uid=version_owner; st->st_size=strlen(version_value); return 0;
}
static ssize_t mock_read(int fd,void *out,size_t n) {
    assert(fd==44); if(version_read_error) { errno=EIO; return -1; } size_t length=strlen(version_value); assert(n>=length); memcpy(out,version_value,length); return (ssize_t)length;
}
static int mock_close(int fd) { assert(fd==44); ++close_count; return 0; }
static int mock_exec(const char *path,char *const argv[],char *const envp[]) {
    ++exec_count; assert(!strcmp(path,"/test/jb/basebin/jbctl"));
    assert(!strcmp(argv[0],path) && !strcmp(argv[1],"package_restart") && argv[2]==NULL);
    assert(envp==expected_environment); errno=exec_error; return -1;
}
#define getuid mock_getuid
#define geteuid mock_geteuid
#define realpath mock_realpath
#define sysctlbyname mock_sysctl
#define lstat mock_lstat
#define open mock_open
#define fstat mock_fstat
#define read mock_read
#define close mock_close
#define execve mock_exec
#include "package_restart.c"
static void reset(void) {
    uid_value=euid_value=helper_owner=version_owner=0;
    exec_count=open_count=close_count=identity_error=identity_malformed=identity_calls=helper_missing=version_open_error=version_read_error=0;
    helper_mode=S_IFREG|0755; version_mode=S_IFREG|0644;
    version_value=PACKAGE_RESTART_VERSION; machine_value="iPhone10,5"; build_value="20H350";
    root_resolves=true; exec_error=ENOENT;
}
int main(void) {
    char *argv[]={"launchctl","reboot","userspace",NULL};
    char *env[]={"TEST=1",NULL}; expected_environment=env;
    const char *binary="/test/jb/usr/bin/launchctl";
    reset(); assert(package_restart_route(binary,"/var/jb",3,argv,env)==ENOENT);
    assert(exec_count==1 && open_count==1 && close_count==1);
    // Missing/old/untrusted helpers fail closed after command matching.
    reset(); helper_missing=1; assert(package_restart_route(binary,"/var/jb",3,argv,env)==ENOENT && !exec_count);
    reset(); version_open_error=1; assert(package_restart_route(binary,"/var/jb",3,argv,env)==ELOOP && !exec_count && !close_count);
    reset(); version_read_error=1; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPROTO && !exec_count && close_count==1);
    reset(); version_value="3.0.10-s2"; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPROTO && !exec_count && close_count==1);
    reset(); version_value="3.0.10-s4\n"; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPERM && !exec_count);
    reset(); helper_mode=S_IFLNK|0755; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPERM && !exec_count);
    reset(); helper_mode=S_IFREG|0775; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPERM && !exec_count);
    reset(); helper_owner=501; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPERM && !exec_count);
    reset(); version_owner=501; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPERM && !exec_count);
    reset(); version_mode=S_IFIFO|0644; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPERM && !exec_count);
    // Every other command, device, identity, UID or path remains untouched.
    reset(); uid_value=501; assert(package_restart_route(binary,"/var/jb",3,argv,env)==0 && !exec_count);
    reset(); euid_value=501; assert(package_restart_route(binary,"/var/jb",3,argv,env)==0 && !exec_count);
    reset(); identity_error=1; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EIO && !exec_count);
    reset(); identity_malformed=1; assert(package_restart_route(binary,"/var/jb",3,argv,env)==EPROTO && !exec_count);
    reset(); machine_value="iPhone10,2"; assert(package_restart_route(binary,"/var/jb",3,argv,env)==0 && !exec_count);
    reset(); build_value="20H349"; assert(package_restart_route(binary,"/var/jb",3,argv,env)==0 && !exec_count);
    reset(); root_resolves=false; assert(package_restart_route(binary,"/test/jb",3,argv,env)==ENOENT && !exec_count);
    reset(); root_resolves=false; assert(package_restart_route("/bin/launchctl","/test/jb",3,argv,env)==0 && !exec_count);
    reset(); identity_error=1; assert(package_restart_route("/bin/launchctl","/var/jb",3,argv,env)==0 && !exec_count && !identity_calls);
    reset(); assert(package_restart_route("/bin/launchctl","/var/jb",3,argv,env)==0 && !exec_count);
    reset(); assert(package_restart_route("/test/jb/usr/bin/not-launchctl","/var/jb",3,argv,env)==0 && !exec_count);
    for (int i=0;i<4;i++) {
        const char *other[]={"system","halt","obliterate","bogus"};
        reset(); argv[2]=(char *)other[i]; assert(package_restart_route(binary,"/var/jb",3,argv,env)==0 && !exec_count);
    }
    argv[2]="userspace";
    reset(); argv[1]="print"; assert(package_restart_route(binary,"/var/jb",3,argv,env)==0 && !exec_count); argv[1]="reboot";
    reset(); assert(package_restart_route(binary,"/var/jb",2,argv,env)==0 && !exec_count);
    reset(); char *extra[]={"launchctl","reboot","userspace","extra",NULL};
    assert(package_restart_route(binary,"/var/jb",4,extra,env)==0 && !exec_count);
    reset(); assert(package_restart_route(binary,"/var/jb",3,NULL,env)==0 && !exec_count);
    reset(); char *missing[]={"launchctl","reboot",NULL,NULL};
    assert(package_restart_route(binary,"/var/jb",3,missing,env)==0 && !exec_count);
    // There is no reboot3 hook or varargs forwarder anywhere in this helper.
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="package-restart-test-") as tmp:
    source=Path(tmp)/"test.c"
    binary=Path(tmp)/"test"
    source.write_text(test)
    subprocess.run(["clang","-std=c11","-Wall","-Wextra","-Werror","-fsanitize=address,undefined","-I",str(root/"src"),str(source),"-o",str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
print("Production package-route tests passed (ASan/UBSan); no exec, reboot, or device actions.")
