#!/usr/bin/env python3
"""Test the production jbctl cleanup reader on the host, without device access."""
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
source = (ROOT / "BaseBin/jbctl/src/main.m").read_text()
start = source.index("static int wait_for_app_cleanup(")
end = source.index("\nvoid print_usage(", start)
helper = source[start:end]
PREAMBLE = r"""
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int interrupt_once, short_reads;
static ssize_t controlled_read(int fd, void *buffer, size_t length) {
    if (interrupt_once) { interrupt_once=0; errno=EINTR; return -1; }
    if (short_reads && length > 1) length=1;
    return read(fd,buffer,length);
}
#define read controlled_read
"""
POSTAMBLE = r"""
static void check(const unsigned char *bytes, size_t length, int expected) {
    int p[2]; assert(pipe(p)==0);
    if(length) assert(write(p[1],bytes,length)==(ssize_t)length);
    close(p[1]);
    char fd[32]; snprintf(fd,sizeof(fd),"%d",p[0]);
    assert(wait_for_app_cleanup(fd)==expected);
    errno=0;assert(fcntl(p[0],F_GETFD)==-1 && errno==EBADF);
}
int main(void) {
    unsigned char modern[]={1,0,0,0}, legacy[]={'w'}, invalid[]={'x'}, corrupt[]={1,0,9,0};
    check(legacy,1,0);check(modern,4,0);
    check(NULL,0,ECANCELED); // Writer closed before any cleanup token.
    for(size_t n=1;n<4;n++) check(modern,n,ECANCELED);
    check(invalid,1,EINVAL);check(corrupt,4,EINVAL);
    interrupt_once=1;short_reads=1;check(modern,4,0);short_reads=0;
    const char *bad[]={"", "-1", "+3", " 3", "3junk", "2147483648", "999999999999999999999999999999999999"};
    assert(wait_for_app_cleanup(NULL)==EINVAL);
    for(size_t i=0;i<sizeof(bad)/sizeof(bad[0]);i++) assert(wait_for_app_cleanup(bad[i])==EINVAL);
    assert(wait_for_app_cleanup("2147483647")==EBADF);
    puts("PASS: legacy/current tokens, EOF cancellation, truncated/invalid tokens, EINTR, short reads, strict fd parsing, descriptor closure");
    return 0;
}
"""
with tempfile.TemporaryDirectory(prefix="dopamine-reader-test-") as directory:
    scratch = pathlib.Path(directory)
    (scratch / "reader.c").write_text(PREAMBLE + helper + POSTAMBLE)
    subprocess.run(["xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", str(scratch / "reader.c"),
                    "-o", str(scratch / "reader")], check=True)
    subprocess.run([str(scratch / "reader")], check=True, timeout=15)
