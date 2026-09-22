# Quartus Prime Lite 20.1.1 on Apple Silicon, via Rosetta.
#
# This is the fast local backend: a full compile of clock_counter takes ~22 s
# here, against ~115 s in the emulated VM and 33 s natively on lyco-server.
# Rosetta translates x86-64 close to native speed, where QEMU's TCG does not.
#
# Two things make it work, and both are non-obvious:
#
# 1. centos:7, for glibc 2.17. Quartus 20.1 targets RHEL 6/7 and its ELF says
#    "for GNU/Linux 2.6.18". On modern glibc (2.31, 2.39) it aborts under
#    Rosetta in malloc's integrity checks -- "mremap_chunk(): invalid pointer",
#    "realloc(): invalid pointer". glibc 2.17 does not perform those checks.
#    No packages need installing: every library Quartus wants is already here.
#
# 2. libudev removed. Quartus dlopens libudev by name (it probes both
#    libudev.so.0 and libudev.so.1, so it already handles absence) and calls
#    udev_enumerate_scan_devices to inventory the machine. Under Rosetta that
#    double-frees inside libudev and takes the process down before synthesis
#    even starts. Deleting it makes Quartus skip the scan. Nothing in the
#    compile flow needs udev -- programming happens on the host, not in here.
#
# Verified 2026-09-21: the .rbf produced here is byte-identical to the one
# lyco-server produces from the same sources.
#
# centos:7 is end-of-life and no longer updated. That is acceptable precisely
# because nothing is installed into it and it never touches the network -- it
# is a fixed ABI, not a maintained system. The image stays in the local Docker
# cache, so the build loop keeps working offline.
FROM --platform=linux/amd64 centos:7

RUN rm -f /lib64/libudev.so.1 /lib64/libudev.so.0

ENV QUARTUS_ROOTDIR=/opt/intelFPGA_lite/20.1/quartus
ENV PATH=/opt/intelFPGA_lite/20.1/quartus/bin:$PATH
ENV HOME=/tmp/qhome
RUN mkdir -p /tmp/qhome && chmod 1777 /tmp/qhome

WORKDIR /work
