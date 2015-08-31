import pdb
import sys

def info(type, value, tb):
    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        sys.__excepthook__(type, value, tb)
    else:
        import traceback
        traceback.print_exception(type, value, tb)
        pdb.pm()

def install_hook():
    sys.excepthook = info
