# Restart coordinator guard checks

Run on macOS with Command Line Tools or Xcode:

```sh
python3 BaseBin/jbctl/tests/test_restart_guards.py
```

The test extracts the production restart coordinator from `src/main.m`, includes the production target/version and service-order headers, and mocks filesystem, identity, spawn, and wait calls. It covers wrong device/build/UID/root/version, invalid file types/ownership, pending updates, lock contention, optional tracing failure, spawn/wait/service errors, descriptor cleanup, and backboardd-last ordering. AddressSanitizer and UndefinedBehaviorSanitizer are enabled. No phone is accessed and no process is signaled.

This does not establish successful iOS injection, package-manager integration, or touchscreen behavior.
