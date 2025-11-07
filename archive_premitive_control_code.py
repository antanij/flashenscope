import os
import time
import cv2
import numpy as np
from pymmcore_plus import CMMCorePlus
import matplotlib.pyplot as plt

print('Talking to μManager...')

# ---- Edit these paths / names if needed ----
mm_path = r"C:\Program Files\Micro-Manager-2.0"
cfg_path = r"C:\Users\Flash\Documents\GitHub\flashenscope\flashenscope.cfg"
camera_name = "HamamatsuHam_DCAM"  # matches your cfg

# ---- Initialize core and load config ----
os.environ["MMCORE_PATH"] = mm_path
core = CMMCorePlus.instance()
core.loadSystemConfiguration(cfg_path)

print("All systems go.")