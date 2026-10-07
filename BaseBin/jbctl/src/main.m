/* Dopamine jbctl by opa334 and contributors (MIT; see LICENSE.md).
 * R3's restart coordinator adapts wumbomumbo/Cheapamine's service selection
 * through cheapamine3.h. Version/target checks, serialization and tracing are
 * additions in this fork. Source lineage and component notices: CREDITS.md.
 */
#import <libjailbreak/libjailbreak.h>
#import <libjailbreak/jbclient_xpc.h>
#import <libjailbreak/jbclient_mach.h>
#import <libjailbreak/stock_fixes.h>
#import "internal.h"

#import <Foundation/Foundation.h>
#import <CoreServices/LSApplicationProxy.h>
#import <CoreServices/LSApplicationWorkspace.h>
#import <cheapamine3.h>
#include <cheapamine3_runtime.h>
#import <sys/utsname.h>
#import <sys/wait.h>
#import <errno.h>
#include <sys/sysctl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <limits.h>
#include <sys/time.h>
#include <time.h>
#include <signal.h>

struct restart_context {
    const char *killallPath;
    int trace;
};

static void restart_trace(int fd, const char *event, int result)
{
    if (fd < 0) return;
    struct timeval now;
    if (gettimeofday(&now, NULL) != 0) return;
    dprintf(fd, "s4 time=%lld.%06d pid=%d event=%s result=%d\n",
        (long long)now.tv_sec, (int)now.tv_usec, getpid(), event, result);
}

static int restart_trace_open(void)
{
    int fd = open("/var/mobile/Media/Cheapamine3-restart.txt",
        O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC, 0644);
    if (fd < 0) return -1;
    struct stat st;
    if (fstat(fd, &st) != 0 || !S_ISREG(st.st_mode) || st.st_uid != 0 || st.st_nlink != 1 ||
        (st.st_size > 65536 && ftruncate(fd, 0) != 0) || fchmod(fd, 0644) != 0) {
        close(fd);
        return -1;
    }
    return fd;
}

static bool restart_version_matches(void)
{
    int fd = open(JBROOT_PATH("/basebin/.version"), O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC);
    if (fd < 0) return false;
    struct stat st;
    char version[sizeof(CHEAPAMINE3_VERSION)] = {0};
    bool valid = fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_uid == 0 &&
        !(st.st_mode & 0022) && st.st_size == sizeof(CHEAPAMINE3_VERSION) - 1;
    ssize_t count = -1;
    if (valid) {
        do { count = read(fd, version, sizeof(version)); } while (count < 0 && errno == EINTR);
    }
    close(fd);
    return valid && count == sizeof(CHEAPAMINE3_VERSION) - 1 &&
        memcmp(version, CHEAPAMINE3_VERSION, sizeof(CHEAPAMINE3_VERSION) - 1) == 0;
}

static int screen_restart_service(const char *name, void *context)
{
	struct restart_context *restart = context;
	const char *killallPath = restart->killallPath;
	pid_t pid = -1;
	int error = exec_cmd_nowait(&pid, killallPath, "-9", name, NULL);
	if (error != 0 || pid <= 0) return error != 0 ? -error : -ECHILD;
	int status = 0;
	while (waitpid(pid, &status, 0) < 0) {
		if (errno != EINTR) return -errno;
	}
	int result = WIFEXITED(status) ? WEXITSTATUS(status) : -EINTR;
	restart_trace(restart->trace, name, result);
	return result;
}

static uint64_t registration_now_ns(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0;
    return (uint64_t)now.tv_sec * 1000000000ULL + (uint64_t)now.tv_nsec;
}

static int register_jailbreak_apps(struct restart_context *context)
{
    // Restore the uicache work normally performed by Dopamine's startup job.
    // Do this in the post-cleanup helper before backboardd refreshes SpringBoard,
    // so failure can be reported without killing the caller or changing services.
    const char *uicache = JBROOT_PATH("/usr/bin/uicache");
    if (access(uicache, X_OK) != 0) return errno ? -errno : -EACCES;
    uint64_t start = registration_now_ns();
    if (!start) return -EIO;
    pid_t pid = -1;
    int error = exec_cmd_nowait(&pid, uicache, "-a", NULL);
    if (error != 0 || pid <= 1) return error != 0 ? (error > 0 ? -error : error) : -ECHILD;
    restart_trace(context->trace, "uicache-started", 0);
    const uint64_t deadline = start + 15000000000ULL;
    int result = -ETIMEDOUT;
    // Both an absolute deadline and iteration cap bound the wait, even if the
    // clock fails. Synchronous system-call/scheduling latency is not controllable.
    for (unsigned iteration = 0; iteration < 1500; iteration++) {
        int status = 0;
        pid_t waited = waitpid(pid, &status, WNOHANG);
        if (waited == pid) return WIFEXITED(status) ? WEXITSTATUS(status) : -ECANCELED;
        if (waited < 0 && errno != EINTR) return -errno;
        uint64_t now = registration_now_ns();
        if (!now) { result = -EIO; break; }
        if (now >= deadline) break;
        usleep(10000);
    }
    // This is our child, not a launchd-owned daemon. Stop only this uicache;
    // never retry registration or fall back to a userspace reboot.
    int stopResult = kill(pid, SIGKILL);
    if (stopResult != 0 && errno != ESRCH)
        restart_trace(context->trace, "uicache-stop-failed", errno);
    // Reap without introducing an unbounded wait after timeout. If the kernel
    // cannot complete exit promptly, jbctl exits and normal parent reaping applies.
    for (unsigned iteration = 0; iteration < 25; iteration++) {
        int status = 0;
        pid_t waited = waitpid(pid, &status, WNOHANG);
        if (waited == pid || (waited < 0 && errno != EINTR)) break;
        usleep(10000);
    }
    return result;
}

static int screen_restart(const char *request)
{
	if (!cheapamine3_target_runtime()) {
		fprintf(stderr, "Screen restart is restricted to iPhone 8 Plus on iOS 16.7.10.\n");
		return 64;
	}
	if (getuid() != 0 || geteuid() != 0 || !gSystemInfo.jailbreakInfo.rootPath) return 77;
	if (!restart_version_matches()) return 78;
	if (getenv("STAGED_JAILBREAK_UPDATE") || getenv("JBUPDATE_NEW_VERSION")) return 78;
	const char *killallPath = JBROOT_PATH("/usr/bin/killall");
	if (access(killallPath, X_OK) != 0) return 69;
	int lock = open(JBROOT_PATH("/basebin/.restart.lock"), O_RDWR | O_CREAT | O_NOFOLLOW | O_CLOEXEC, 0600);
	if (lock < 0) return 75;
	struct stat lockStat;
	if (fstat(lock, &lockStat) != 0 || !S_ISREG(lockStat.st_mode) || lockStat.st_uid != 0 ||
	    lockStat.st_nlink != 1 || (lockStat.st_mode & 0022) || flock(lock, LOCK_EX | LOCK_NB) != 0) {
		close(lock);
		return 75;
	}
	struct restart_context context = {.killallPath = killallPath, .trace = restart_trace_open()};
	restart_trace(context.trace, request, 0);
	int result = 0;
    bool registrationFailed = false;
    if (!strcmp(request, "screen_restart")) {
        result = register_jailbreak_apps(&context);
        restart_trace(context.trace, "uicache-complete", result);
        registrationFailed = result != 0;
        if (registrationFailed)
            fprintf(stderr, "Jailbreak app registration failed (%d); service restart was not attempted.\n", result);
    }
    if (result == 0) result = cheapamine3_restart(screen_restart_service, &context);
	restart_trace(context.trace, "complete", result);
	if (context.trace >= 0) close(context.trace);
	close(lock);
	if (result != 0) fprintf(stderr, "Screen restart failed (%d); no userspace reboot attempted.\n", result);
	return registrationFailed ? 71 : (result == 0 ? 0 : 70);
}

int reboot3(uint64_t flags, ...);
#define RB2_USERREBOOT (0x2000000000000000llu)
extern char **environ;

// Accept the legacy one-byte 'w' or the current uint32_t value 1.
// EOF is cancellation, never permission to perform the requested action.
static int wait_for_app_cleanup(const char *fdArgument)
{
    if (!fdArgument || !fdArgument[0]) return EINVAL;
    for (const char *p = fdArgument; *p; p++) {
        if (*p < '0' || *p > '9') return EINVAL;
    }
    errno = 0;
    char *end = NULL;
    long parsed = strtol(fdArgument, &end, 10);
    if (errno == ERANGE || *end || parsed < 0 || parsed > INT_MAX) return EINVAL;
    int fd = (int)parsed;
    uint8_t token[sizeof(uint32_t)] = {0};
    size_t received = 0, required = 1;
    int result = 0;
    while (received < required) {
        ssize_t count = read(fd, token + received, required - received);
        if (count < 0) {
            if (errno == EINTR) continue;
            result = errno;
            break;
        }
        if (count == 0) { result = ECANCELED; break; }
        received += (size_t)count;
        if (received == 1) {
            if (token[0] == 'w') break;
            if (token[0] != 1) { result = EINVAL; break; }
            required = sizeof(token);
        }
    }
    if (result == 0 && required == sizeof(token)) {
        uint32_t value;
        memcpy(&value, token, sizeof(value));
        if (value != 1) result = EINVAL;
    }
    close(fd);
    return result;
}

void print_usage(void)
{
	printf("Usage: jbctl <command> <arguments>\n\
Available commands:\n\
	proc_set_debugged <pid>\t\tMarks the process with the given pid as being debugged, allowing invalid code pages inside of it\n\
	trustcache info\t\t\tPrint info about all jailbreak related trustcaches and the cdhashes contained in them\n\
	trustcache clear\t\tClears all existing cdhashes from the jailbreaks trustcache\n\
	trustcache add <cdhash>\t\tAdd an arbitrary cdhash to the jailbreaks trustcache\n\
	update <tipa/basebin/tarball> <path>\tInitiates a jailbreak update either based on a TIPA, based on a basebin.tar file or based on a standalone tarball, TIPA installation depends on TrollStore, afterwards it triggers a userspace reboot\n");
}

int main(int argc, char* argv[])
{
	if (!strcmp(argv[argc-1], "earlyboot")) {
		// If jbctl is spawned in "early boot" state, the jbserver port needs to be obtained from registeredPorts[0] instead
		mach_port_t *registeredPorts;
		mach_msg_type_number_t registeredPortsCount = 0;
		if (mach_ports_lookup(mach_task_self(), &registeredPorts, &registeredPortsCount) == KERN_SUCCESS) {
			jbclient_xpc_set_custom_port(registeredPorts[0]);

			for(mach_msg_type_number_t i = 1; i < registeredPortsCount; i++) {
				mach_port_deallocate(mach_task_self(), registeredPorts[i]);
			}
			vm_deallocate(mach_task_self(), (vm_address_t)registeredPorts, registeredPortsCount * sizeof(mach_port_t));
		}
	}

	setvbuf(stdout, NULL, _IOLBF, 0);
	if (argc < 2) {
		print_usage();
		return 1;
	}

	if (getuid() != 0 && geteuid() == 0) {
		// When jailbroken the Dopamine app cannot have uid 0 because it can't drop it anymore without loosing it
		// So in some cases (e.g. for spawning dpkg) we need to use jbctl to get it
		setuid(0);
	}

	if (argc > 2) {
		if (!strcmp(argv[argc-2], "--waitfor")) {
            int error = wait_for_app_cleanup(argv[argc-1]);
            if (error != 0) {
                fprintf(stderr, "jbctl: app cleanup handoff failed: %s\n", strerror(error));
                return 1;
            }
		}
	}

	const char *rootPath = jbclient_get_jbroot();
	if (rootPath) {
		gSystemInfo.jailbreakInfo.rootPath = strdup(rootPath);
	}

	char *cmd = argv[1];
	if (!strcmp(cmd, "proc_set_debugged")) {
		if (argc != 3) {
			print_usage();
			return 1;
		}
		int pid = atoi(argv[2]);
		int64_t result = jbclient_platform_set_process_debugged(pid, true);
		if (result == 0) {
			printf("Successfully marked proc of pid %d as debugged\n", pid);
		}
		else {
			printf("Failed to mark proc of pid %d as debugged\n", pid);
		}
	}
	else if (!strcmp(cmd, "trustcache")) {
		if (argc < 3) {
			print_usage();
			return 2;
		}
		if (getuid() != 0) {
			printf("ERROR: trustcache subcommand requires root.\n");
			return 3;
		}
		const char *trustcacheCmd = argv[2];
		if (!strcmp(trustcacheCmd, "info")) {
			xpc_object_t tcArr = nil;
			if (jbclient_root_trustcache_info(&tcArr) == 0) {
				size_t tcCount = xpc_array_get_count(tcArr);
				for (size_t i = 0; i < tcCount; i++) {
					xpc_object_t tc = xpc_array_get_dictionary(tcArr, i);
					size_t uuidLength = 0;
					const void *uuidData = xpc_dictionary_get_data(tc, "uuid", &uuidLength);
					xpc_object_t cdhashesArr = xpc_dictionary_get_array(tc, "cdhashes");
					if (uuidData && cdhashesArr) {
						size_t length = xpc_array_get_count(cdhashesArr);
						char uuidString[uuidLength * 2 + 1];
						convert_data_to_hex_string(uuidData, uuidLength, uuidString);
						printf("Jailbreak Trustcache %zd <UUID: %s> (length: %zd)\n", i, uuidString, length);
						for (size_t j = 0; j < length; j++) {
							size_t cdhashLength = 0;
							const void *cdhashData = xpc_array_get_data(cdhashesArr, j, &cdhashLength);
							if (cdhashData) {
								char cdhashString[cdhashLength * 2 + 1];
								convert_data_to_hex_string(cdhashData, cdhashLength, cdhashString);
								printf("| %zd:\t%s\n", j+1, cdhashString);
							}
						}
					}
				}
			}
			return 0;
		}
		else if (!strcmp(trustcacheCmd, "clear")) {
			return jbclient_root_trustcache_clear();
		}
		else if (!strcmp(trustcacheCmd, "add")) {
			if (argc < 4) {
				print_usage();
				return 2;
			}
			const char *cdhashString = argv[3];
			if (strlen(cdhashString) != (sizeof(cdhash_t) * 2)) {
				printf("ERROR: passed cdhash has wrong length\n");
				return 2;
			}
			cdhash_t cdhash;
			if (convert_hex_string_to_data(cdhashString, &cdhash)) {
				printf("ERROR: passed cdhash is malformed\n");
				return 2;
			}
			return jbclient_root_trustcache_add_cdhash(cdhash, sizeof(cdhash));
		}
	}
	else if (!strcmp(cmd, "reboot_userspace")) {
		return reboot3(RB2_USERREBOOT);
	}
	else if (!strcmp(cmd, "screen_restart") || !strcmp(cmd, "package_restart")) {
		return screen_restart(cmd);
	}
	else if (!strcmp(cmd, "respring")) {
		const char *sbreloadPath = JBROOT_PATH("/usr/bin/sbreload");
		if (execve(sbreloadPath, (char *[]){ (char *)sbreloadPath, NULL }, environ) != 0) {
			killall("/usr/libexec/backboardd", SIGTERM);
		}
	}
	else if (!strcmp(cmd, "rebuild_icon_cache")) {
		BOOL suc = [[LSApplicationWorkspace defaultWorkspace] _LSPrivateRebuildApplicationDatabasesForSystemApps:YES internal:YES user:YES];
		return suc ? 0 : -1;
	}
	else if (!strcmp(cmd, "update")) {
		if (cheapamine3_target_runtime()) {
			fprintf(stderr, "This compatibility build updates after a full device restart and re-jailbreak; no live update was staged.\n");
			return 78;
		}
		if (argc < 4) {
			print_usage();
			return 2;
		}
		char *updateType = argv[2];
		char *updateFile = argv[3];
		if (access(updateFile, F_OK) != 0) {
			printf("ERROR: File %s does not exist\n", updateFile);
			return 3;
		}

		if (!strcmp(updateType, "tipa")) {
			setsid();

			LSApplicationProxy *trollstoreAppProxy = [LSApplicationProxy applicationProxyForIdentifier:@"com.opa334.TrollStore"];
			if (!trollstoreAppProxy || !trollstoreAppProxy.installed) {
				printf("Unable to locate TrollStore, doesn't seem like it's installed.\n");
				return 4;
			}
			NSString *trollstorehelperPath = [trollstoreAppProxy.bundleURL.path stringByAppendingPathComponent:@"trollstorehelper"];
			int r = exec_cmd(trollstorehelperPath.fileSystemRepresentation, "install", "skip-uicache", "force", updateFile, NULL);
			if (r != 0) {
				printf("Failed to install tipa via TrollStore: %d\n", r);
				return 5;
			}

			LSApplicationProxy *dopamineAppProxy = [LSApplicationProxy applicationProxyForIdentifier:@"com.opa334.Dopamine"];
			if (!dopamineAppProxy) {
				printf("Unable to locate newly installed Dopamine build.\n");
				return 6;
			}
			updateFile = strdup([dopamineAppProxy.bundleURL.path stringByAppendingPathComponent:@"basebin.tar"].fileSystemRepresentation);
			// Fall through to basebin installation
		}
		else if (!strcmp(updateType, "tarball")) {
			NSString *tmpPath = [@"/tmp" stringByAppendingPathComponent:[NSUUID UUID].UUIDString];
			[[NSFileManager defaultManager] createDirectoryAtPath:tmpPath withIntermediateDirectories:NO attributes:nil error:nil];
			int r = libarchive_unarchive(updateFile, tmpPath.fileSystemRepresentation);
			if (r != 0) {
				printf("Failed to extract tarball: %d\n", r);
				return 7;
			}
			updateFile = strdup([tmpPath stringByAppendingPathComponent:@"basebin.tar"].fileSystemRepresentation);
			// Fall through to basebin installation
		}
		else if (strcmp(updateType, "basebin") != 0) {
			// If type is not tipa, tarball or basebin, bail out
			print_usage();
			return 2;
		}

		int64_t result = jbclient_platform_stage_jailbreak_update(updateFile);
		if (result == 0) {
			printf("Staged update for installation during the next userspace reboot, userspace rebooting now...\n");
			usleep(10000);
			return reboot3(RB2_USERREBOOT);
		}
		else {
			printf("Staging update failed with error code %lld\n", result);
			return result;
		}
	}
	else if (!strcmp(cmd, "internal")) {
		if (getuid() != 0) return 41;
		if (argc < 3) return 42;

		const char *internalCmd = argv[2];
		return jbctl_handle_internal(internalCmd, argc-2, &argv[2]);
	}

	return 0;
}
