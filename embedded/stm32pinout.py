#!/usr/bin/env python3
#########################################################################
# Copyright 2020 Matthijs Kooijman <matthijs@stdin.nl>
#
# Permission is hereby granted, free of charge, to anyone obtaining a
# copy of this document and accompanying files, to do whatever they want
# with them without any restriction, including, but not limited to,
# copying, modification and redistribution.
#
# NO WARRANTY OF ANY KIND IS PROVIDED.
#
#########################################################################
# This script is intended to generate a CSV listing of pins for a given
# STM32 MCU, along with all the special functions that can are available
# on that pin. This listing can then be used to decide on and document a
# pin mapping for a given project.
#
# This listing includes both the "Alternate functions" (such as timer
# outputs or SPI buses) that must be explicitly mapped using the AF pin
# mode, and "Additional functions" (such as ADC, EXTI or DAC) that are
# automatically connected when the relevant peripheral is enabled.
#
# This script was written because the tables from the datasheet cannot
# be easily copy-pasted (and the datasheet has the alternate and
# additional functions in two separate tables), and the STM32CubeMX
# software can only seem to export a pinout table with alternate
# functions, not additional functions.
#
# To run this script, you will need the XML file for the MCU you are
# interested in from inside the CubeMX installation. Currently, these
# only seem to be distributed by ST as part of CubeMX, though there
# might be others redistributing them separately (but at the time of
# writing, Dec 2020, I found on github repo that wasn't updated in over
# a year).
#
# For example, you can run this script as follows:
#
#     ./stm32pinout.py /usr/local/cubemx/db/mcu/STM32F103CBUx.xml
#
# This generates a CSV table with all pins on stdout.
#########################################################################

import argparse
import csv
import itertools
import re
import sys
from xml.etree import ElementTree


# Default GPIO modes that do not need to be mentioned in the output
DEFAULT_GPIO_MODES = {'Input', 'Output', 'Analog'}
# Sort signal types in this order
ORDER = ["GPIO", "EXTI", "ADC", "DAC", "TIM", "LPTIM", "UART", "USART", "LPUART", "SPI", "I2C"]

# TODO: It could be good to (also) support sorting signals by AF index.
# This requires reading from one more xml file, see
# https://community.st.com/s/question/0D53W00000JMY0USAX/how-to-extract-alternate-function-mappings-from-cubemxs-xml-database-files
# TODO: Can we do even smarter sorting of function names? So that
# related signals (e.g. I2C1_SDA and I2C_SCL) end up vertically
# adjacent? Also requires sorting pins in this script (i.e. on pin no or
# pin name), otherwise sorting afterwards breaks the alignment. Probably
# a non-trivial optimization problem, though.
# TODO: Can we also include pin structure (e.g. 5V tolerant FT, or TT,
# etc.)? Not sure if this is stored in the XML files anywhere, though...


def main():
    parser = argparse.ArgumentParser(
        description='Converts an STM32CubeMX MCU description XML into a pinout CSV. Writes to stdout.'
    )
    parser.add_argument('filename', type=str,
                        help='The file to parse, e.g. /path/to/cubemx/db/mcu/STM32F103CBUx.xml')
    args = parser.parse_args()

    writer = csv.writer(sys.stdout)

    root = ElementTree.parse(args.filename).getroot()

    # This extracts the default namespace (xmlns="") from the root
    # element, as that is implicitly prefixed on all elements. By
    # putting that into NAMESPACES and passing that to all find calls,
    # the tag names in our find queries are also prefixed with the same
    # ns and will actually match.
    NAMESPACES = {}
    match = re.match(r'{(.*)}.*', root.tag)
    if match:
        NAMESPACES[''] = match.group(1)
    else:
        sys.stderr.write("WARNING: No xmlns tag found in root element\n")

    writer.writerow(('name', 'pin', 'type'))
    for elem in root.iterfind('Pin', NAMESPACES):
        signals = []
        for signal in elem.iterfind('Signal', NAMESPACES):
            name = signal.attrib['Name']
            if name == 'GPIO':
                modes = set(signal.attrib.get('IOModes', '').split(','))

                # I suppose this never happens, but better be explicit than silently hide information
                missing = DEFAULT_GPIO_MODES - modes
                if missing:
                    name += '({})'.format(','.join(mode + '_Not_Supported' for mode in missing))

                # For GPIO pins, things like EXTI or EVENTOUT are stored in IOModes
                for mode in modes - DEFAULT_GPIO_MODES:
                    signals.append(mode)

            signals.append(name)

        def sortkey(signal):
            for weight, prefix in enumerate(ORDER):
                if signal.startswith(prefix):
                    return (weight, signal)
            return (len(ORDER), signal)

        writer.writerow(itertools.chain(
            [elem.attrib['Name'], elem.attrib['Position'], elem.attrib['Type']],
            sorted(signals, key=sortkey),
        ))


main()
