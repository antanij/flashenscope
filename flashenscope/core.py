# flashenscope/core.py
from pymmcore_plus import CMMCorePlus

# Create a single global instance
_mmc = None

def get_core():
    """
    Returns a global instance of CMMCorePlus.
    Initializes it if not already done.
    """
    global _mmc
    if _mmc is None:
        _mmc = CMMCorePlus.instance()
        _mmc.loadSystemConfiguration(r"C:\Users\Flash\Documents\GitHub\flashenscope\flashenscope.cfg")
        print("✅ Micro-Manager core initialized.")
    return _mmc

def reload_core():
    """
    Force a reload of the core configuration.
    """
    global _mmc
    _mmc = None
    return get_core()

def core():
    """
    Alias for get_core(), for convenience.
    """
    return get_core()
