#!/usr/bin/env python3

# AVR / Arduino dynamic memory log analyis script.
#
# Copyright 2014 Matthijs Kooijman <matthijs@stdin.nl>
#
# Permission is hereby granted, free of charge, to anyone obtaining a
# copy of this document and accompanying files, to do whatever they want
# with them without any restriction, including, but not limited to,
# copying, modification and redistribution.
#
# NO WARRANTY OF ANY KIND IS PROVIDED.

# This script is meant to analyze the output of the corresponding
# Arduino-side malloc, realloc and free logging code. It mostly checks
# for double free problems, and also gives a list of allocations not
# freed at the end.
#
# To run it, feed the log output into stdin, the analysis result will
# appear on stdout.

import io
import re
import sys
import collections

allocations = {}

Allocation = collections.namedtuple('Allocation', ['line', 'lineno', 'size'])

infile = io.TextIOWrapper(sys.stdin.buffer, encoding='latin-1')

for n, line in enumerate(infile.readlines()):
    # Make lines 1-based instead of 0-based
    n += 1

    match = re.match(r"^malloc\(([0-9]+)\) = (0x[0-9A-F]+)$", line)
    if match:
        allocations[match.group(2)] = Allocation(line = line, lineno = n, size = int(match.group(1)))
        continue

    match = re.match(r"^realloc\((0x[0-9A-F]+), ([0-9]+)\) = (0x[0-9A-F]+)$", line)
    if match:
        if match.group(1) != '0x0':
            try:
                allocations.pop(match.group(1))
            except KeyError:
                sys.stdout.write("{:3d}: {}".format(n, line))
                sys.stdout.write(">> {} not allocated\n".format(match.group(1)))
                continue

        allocations[match.group(3)] = Allocation(line = line, lineno = n, size = int(match.group(2)))
        continue

    match = re.match(r"^free\((0x[0-9A-F]+)\)$", line)
    if match:
        if (match.group(1) == '0x0'):
            continue
        try:
            allocations.pop(match.group(1))
        except KeyError:
            sys.stdout.write("{:3d}: {}".format(n, line))
            sys.stdout.write(">> {} not allocated\n".format(match.group(1)))
            continue

        continue

for addr, alloc in allocations.items():
    sys.stdout.write("{:3d}: {}".format(alloc.lineno, alloc.line))
    sys.stdout.write(">> {} never freed\n".format(addr))
