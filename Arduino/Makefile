# Copyright 2014 Matthijs Kooijman <matthijs@stdin.nl>
#
# Permission is hereby granted, free of charge, to anyone obtaining a
# copy of this document and accompanying files, to do whatever they want
# with them without any restriction, including, but not limited to,
# copying, modification and redistribution.
#
# NO WARRANTY OF ANY KIND IS PROVIDED.

MAIN=$(abspath $(firstword $(wildcard *.ino)))
BOARD=pinoccio:avr:pinoccio
PORT=/dev/ttyACM0
BUILD_DIR=$(abspath build)
PREFS=--pref "build.path=$(BUILD_DIR)"

-include Makefile.local

compile:
	mkdir -p $(BUILD_DIR)
	arduino-git $(PREFS) --verbose --verify --board $(BOARD) --port $(PORT) $(MAIN)

upload:
	mkdir -p $(BUILD_DIR)
	pkill minicom -F /var/lock/LCK..$(notdir $(PORT)) || true
	arduino-git $(PREFS) --verbose --upload --board $(BOARD) --port $(PORT) $(MAIN)
	pkill --signal USR1 arduinoconsole -F $(HOME)/.arduino/console.$(notdir $(PORT)).pid || true

disasm: compile
	avr-objdump --disassemble --source --demangle $(BUILD_DIR)/*.elf
