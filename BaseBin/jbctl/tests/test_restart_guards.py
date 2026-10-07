#!/usr/bin/env python3
"""Exercise the actual restart coordinator with mocked syscalls; no device or signals."""
from pathlib import Path
import subprocess
import tempfile

basebin = Path(__file__).resolve().parents[2]
source = (basebin / "jbctl/src/main.m").read_text()
start = source.index("struct restart_context {")
end = source.index("\nint reboot3(", start)
production = source[start:end]
preamble = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <sys/file.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <time.h>
#include <signal.h>
static struct { struct { const char *rootPath; } jailbreakInfo; } gSystemInfo;
#define JBROOT_PATH(path) "/test/jb" path
static const char *machine, *build, *version;
static uid_t uid_value, euid_value, version_owner, lock_owner;
static mode_t version_type, lock_type;
static int identity_error, version_read_interrupt, version_read_error, lock_busy, staged;
static int no_killall, trace_error, spawned, fail_spawn, failed_service, service_code, wait_interrupt;
static int opened, closed, trace_lines, version_flags, trace_flags, lock_flags;
static int invalid_child_pid, signaled_child;
static int registration_required, registration_spawned, registration_done, registration_code;
static int registration_spawn_error, registration_invalid_pid, registration_wait_error, registration_wait_interrupt;
static int registration_timeout, registration_signaled, registration_kills, registration_clock_error, registration_missing;
static int registration_cleanup_stuck, registration_waits, registration_pause_count, registration_kill_error;
static uint64_t registration_clock;
static int mock_sysctl(const char *name, void *out, size_t *size, void *in, size_t length) {
    assert(in==NULL && length==0);
    if(identity_error) {errno=EIO;return -1;}
    const char *value=!strcmp(name,"hw.machine")?machine:build;
    assert(*size>strlen(value));memcpy(out,value,strlen(value)+1);*size=strlen(value)+1;return 0;
}
static uid_t mock_getuid(void) {return uid_value;}
static uid_t mock_geteuid(void) {return euid_value;}
static char *mock_getenv(const char *key) {
    if(!strcmp(key,"STAGED_JAILBREAK_UPDATE")) return staged==1?"pending":NULL;
    if(!strcmp(key,"JBUPDATE_NEW_VERSION")) return staged==2?"pending":NULL;
    assert(false);return NULL;
}
static int mock_open(const char *path,int flags,...) {
    int fd;
    if(!strcmp(path,"/test/jb/basebin/.version")) {fd=10;version_flags=flags;}
    else if(!strcmp(path,"/test/jb/basebin/.restart.lock")) {fd=11;lock_flags=flags;}
    else {assert(!strcmp(path,"/var/mobile/Media/Cheapamine3-restart.txt"));trace_flags=flags;if(trace_error){errno=EACCES;return -1;}fd=12;}
    ++opened;return fd;
}
static int mock_fstat(int fd,struct stat *st) {
    memset(st,0,sizeof(*st));st->st_nlink=1;
    if(fd==10) {st->st_mode=version_type|0644;st->st_uid=version_owner;st->st_size=(off_t)strlen(version);}
    else if(fd==11) {st->st_mode=lock_type|0600;st->st_uid=lock_owner;}
    else {assert(fd==12);st->st_mode=S_IFREG|0644;}
    return 0;
}
static ssize_t mock_read(int fd,void *out,size_t size) {
    assert(fd==10);
    if(version_read_interrupt) {version_read_interrupt=0;errno=EINTR;return -1;}
    if(version_read_error) {errno=EIO;return -1;}
    assert(size>=strlen(version));memcpy(out,version,strlen(version));return (ssize_t)strlen(version);
}
static int mock_close(int fd) {assert(fd>=10 && fd<=12);++closed;return 0;}
static int mock_flock(int fd,int operation) {assert(fd==11 && operation==(LOCK_EX|LOCK_NB));if(lock_busy){errno=EWOULDBLOCK;return -1;}return 0;}
static int mock_access(const char *path,int mode) {
    assert(mode==X_OK);
    if(!strcmp(path,"/test/jb/usr/bin/uicache")) {if(registration_missing){errno=ENOENT;return -1;}return 0;}
    assert(!strcmp(path,"/test/jb/usr/bin/killall"));return no_killall?-1:0;
}
static int mock_ftruncate(int fd,off_t size) {assert(fd==12 && size==0);return 0;}
static int __attribute__((unused)) mock_fchmod(int fd,mode_t mode) {assert(fd==12 && mode==0644);return 0;}
static int mock_dprintf(int fd,const char *format,...) {assert(fd==12 && format);++trace_lines;return 1;}
static const char *services[]={"mediaserverd","installd","userd","networkd","backboardd"};
static int mock_spawn(pid_t *pid,const char *path,...) {
    if(!strcmp(path,"/test/jb/usr/bin/uicache")) {
        assert(registration_required && spawned==0 && registration_spawned==0);
        va_list args;va_start(args,path);assert(!strcmp(va_arg(args,const char *),"-a"));assert(va_arg(args,void *)==NULL);va_end(args);
        ++registration_spawned;*pid=registration_invalid_pid?(registration_invalid_pid==1?1:registration_invalid_pid==2?0:-1):124;return registration_spawn_error?ENOENT:0;
    }
    assert(!strcmp(path,"/test/jb/usr/bin/killall"));
    assert(!registration_required || registration_done);
    va_list args;va_start(args,path);assert(!strcmp(va_arg(args,const char *),"-9"));
    assert(spawned<5 && !strcmp(va_arg(args,const char *),services[spawned]));assert(va_arg(args,void *)==NULL);va_end(args);
    ++spawned;*pid=invalid_child_pid?-1:123;
    return fail_spawn==spawned?ENOENT:0;
}
static pid_t mock_wait(pid_t pid,int *status,int flags) {
    if(pid==124) {
        assert(flags==WNOHANG); ++registration_waits;
        if(registration_wait_interrupt){registration_wait_interrupt=0;errno=EINTR;return -1;}
        if(registration_wait_error){errno=ECHILD;return -1;}
        if(registration_timeout && (!registration_kills || registration_cleanup_stuck || registration_kill_error))return 0;
        *status=(registration_signaled||registration_kills)?SIGKILL:(registration_code<<8);
        registration_done=registration_code==0 && !registration_signaled && !registration_kills;return pid;
    }
    assert(pid==123 && flags==0);
    if(wait_interrupt) {wait_interrupt=0;errno=EINTR;return -1;}
    *status=signaled_child?SIGTERM:((failed_service==spawned?service_code:0)<<8);return pid;
}
static int mock_clock_gettime(clockid_t which,struct timespec *now) {
    assert(which==CLOCK_MONOTONIC);if(registration_clock_error){errno=EIO;return -1;}
    now->tv_sec=registration_clock/1000000000ULL;now->tv_nsec=registration_clock%1000000000ULL;return 0;
}
static int mock_usleep(useconds_t micros) {assert(micros==10000);registration_clock+=(uint64_t)micros*1000; ++registration_pause_count;return 0;}
static int mock_kill(pid_t pid,int signal) {assert(pid==124 && signal==SIGKILL);assert(registration_kills==0);++registration_kills;if(registration_kill_error){errno=EPERM;return -1;}return 0;}
#define clock_gettime mock_clock_gettime
#define usleep mock_usleep
#define kill mock_kill
#define sysctlbyname mock_sysctl
#define getuid mock_getuid
#define geteuid mock_geteuid
#define getenv mock_getenv
#define open mock_open
#define fstat mock_fstat
#define read mock_read
#define close mock_close
#define flock mock_flock
#define access mock_access
#define ftruncate mock_ftruncate
#define fchmod mock_fchmod
#define dprintf mock_dprintf
#define exec_cmd_nowait mock_spawn
#define waitpid mock_wait
#include <cheapamine3.h>
#include <cheapamine3_runtime.h>
'''
postamble = r'''
static void reset(void) {
    machine="iPhone10,5";build="20H350";version=CHEAPAMINE3_VERSION;
    gSystemInfo.jailbreakInfo.rootPath="/test/jb";
    uid_value=euid_value=version_owner=lock_owner=0;version_type=lock_type=S_IFREG;
    identity_error=version_read_interrupt=version_read_error=lock_busy=staged=no_killall=trace_error=0;
    spawned=fail_spawn=failed_service=service_code=wait_interrupt=opened=closed=trace_lines=0;
    version_flags=trace_flags=lock_flags=invalid_child_pid=signaled_child=0;
    registration_required=registration_spawned=registration_done=registration_code=0;
    registration_spawn_error=registration_invalid_pid=registration_wait_error=registration_wait_interrupt=0;
    registration_timeout=registration_signaled=registration_kills=registration_clock_error=registration_missing=0;
    registration_cleanup_stuck=registration_waits=registration_pause_count=registration_kill_error=0;registration_clock=1000000000ULL;
}
static void check(int expected,int expected_spawned) {
    assert(screen_restart("package_restart")==expected);
    assert(spawned==expected_spawned && opened==closed);
}
int main(void) {
    reset();check(0,5);assert(trace_lines==7);
    assert((version_flags&O_NOFOLLOW) && (version_flags&O_NONBLOCK));
    assert((trace_flags&O_NOFOLLOW) && (trace_flags&O_NONBLOCK));
    assert((lock_flags&O_NOFOLLOW) && (lock_flags&O_CLOEXEC));
    reset();machine="iPhone10,2";check(64,0);
    reset();build="20H349";check(64,0);
    reset();identity_error=1;check(64,0);
    reset();uid_value=501;check(77,0);
    reset();euid_value=501;check(77,0);
    reset();gSystemInfo.jailbreakInfo.rootPath=NULL;check(77,0);
    reset();version="3.0.10-s2";check(78,0);
    reset();version=CHEAPAMINE3_VERSION "\n";check(78,0);
    reset();version_owner=501;check(78,0);
    reset();version_type=S_IFREG|0020;check(78,0);
    reset();version_type=S_IFIFO;check(78,0);
    reset();version_read_error=1;check(78,0);
    reset();version_read_interrupt=1;check(0,5);
    reset();staged=1;check(78,0);
    reset();staged=2;check(78,0);
    reset();no_killall=1;check(69,0);
    reset();lock_owner=501;check(75,0);
    reset();lock_type=S_IFREG|0020;check(75,0);
    reset();lock_type=S_IFIFO;check(75,0);
    reset();lock_busy=1;check(75,0);
    reset();trace_error=1;check(0,5);assert(trace_lines==0);
    reset();fail_spawn=2;check(70,2);
    reset();invalid_child_pid=1;check(70,1);
    reset();signaled_child=1;check(70,1);
    reset();failed_service=2;service_code=2;check(70,2);
    reset();failed_service=2;service_code=1;check(0,5);
    reset();failed_service=5;service_code=1;check(70,5);
    reset();wait_interrupt=1;check(0,5);
    reset();registration_required=1;assert(screen_restart("screen_restart")==0);
    assert(registration_spawned==1 && registration_done && spawned==5 && !registration_kills && opened==closed && trace_lines==9);
    reset();registration_required=1;registration_missing=1;assert(screen_restart("screen_restart")==71 && !registration_spawned && !spawned && opened==closed);
    reset();registration_required=1;registration_clock_error=1;assert(screen_restart("screen_restart")==71 && !registration_spawned && !spawned);
    reset();registration_required=1;registration_spawn_error=1;assert(screen_restart("screen_restart")==71 && registration_spawned==1 && !spawned && !registration_kills);
    reset();registration_required=1;registration_invalid_pid=1;assert(screen_restart("screen_restart")==71 && !spawned && !registration_kills);
    reset();registration_required=1;registration_invalid_pid=2;assert(screen_restart("screen_restart")==71 && !spawned && !registration_kills);
    reset();registration_required=1;registration_invalid_pid=3;assert(screen_restart("screen_restart")==71 && !spawned && !registration_kills);
    reset();registration_required=1;registration_code=3;assert(screen_restart("screen_restart")==71 && !spawned && !registration_kills);
    reset();registration_required=1;registration_signaled=1;assert(screen_restart("screen_restart")==71 && !spawned && !registration_kills);
    reset();registration_required=1;registration_wait_error=1;assert(screen_restart("screen_restart")==71 && !spawned && !registration_kills);
    reset();registration_required=1;registration_wait_interrupt=1;assert(screen_restart("screen_restart")==0 && spawned==5 && registration_done);
    reset();registration_required=1;registration_timeout=1;assert(screen_restart("screen_restart")==71 && !spawned && registration_spawned==1 && registration_kills==1 && registration_waits<=1525 && opened==closed);
    reset();registration_required=1;registration_timeout=registration_cleanup_stuck=1;assert(screen_restart("screen_restart")==71 && !spawned && registration_kills==1 && registration_pause_count<=1525 && opened==closed);
    reset();registration_required=1;registration_timeout=registration_kill_error=1;assert(screen_restart("screen_restart")==71 && !spawned && registration_kills==1 && registration_pause_count<=1525 && opened==closed);
    reset();check(0,5);assert(!registration_spawned); // Sileo package restart stays unchanged.
    puts("Restart coordinator guards/order/failures and registration passed (ASan/UBSan); no real process signals.");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="cheapamine-restart-test-") as directory:
    tmp = Path(directory)
    (tmp / "test.c").write_text(preamble + production + postamble)
    subprocess.run(["xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", "-I", str(basebin / "_external/include"),
                    str(tmp / "test.c"), "-o", str(tmp / "test")], check=True)
    result = subprocess.run([str(tmp / "test")], capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    print(result.stdout, end="")
