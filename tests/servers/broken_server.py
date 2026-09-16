"""A server that fails on startup, for testing how the library reports it."""

import sys

sys.stderr.write("FATAL: the configuration file could not be read\n")
sys.stderr.flush()
sys.exit(1)
