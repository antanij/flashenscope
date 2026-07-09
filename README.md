# flashenscope

Python scripts to control a fully motorized Nikon Ti microscope equipped with a Hamamatsu ORCA-Flash4.0 V3 camera. This repository relies on **Micro-Manager** and **pymmcore_plus** for hardware orchestration.

## Motorized Components Controlled
* **Nikon Ti Microscope:** Nosepiece (objectives, Z-drive, PFS), filter turret, and halogen lamp
* **Camera:** Hamamatsu ORCA-Flash4.0 V3
* **Light Sources:** Lumencor SOLA light engine and Sutter shutter for Nikon's halogen
* **Stage Controller:** Ludl M6000 (XY control)

---

## ⚙️ Installation

### 1. Prerequisites & Dependencies
- Ensure you have Micro-Manager installed and configured with your hardware configuration file (e.g., `flashenscope.cfg`).
- All dependencies will be installed by the following steps.

### 2. Environment Setup
Open your terminal or Anaconda Prompt and run the following commands to create the environment and install the package in editable mode:

```bash
# Create and activate the conda environment
conda create -n flash python=3.10 -y
conda activate flash

# Navigate to your local repository directory
cd /d C:\Users\Flash\Documents\GitHub\flashenscope

# Install the package in editable mode
pip install -e . --use-pep517
```

---

## 🚀 Quick Start & Code Instances

You can find copy-ready code snippets inside `cheat_sheet.py`. To start an interactive session:

```bash
conda activate flash
jupyter lab
# OR launch python directly
python
```

### 1. Initialize the Microscope
Establish communication with the microscope and all connected peripherals.

```python
import flashenscope as fs

# Initialize connections
mmc = fs.initialize()
# Wait for the console message: "All systems go!"
```

### 2. Slow Time-Lapse Imaging
For standard or slow interval time-lapses, leverage Python's native timing and saving libraries.

```python
import time
import tifffile

# Capture a single frame using a preset configuration
im = fs.takePicture('tr_10x_20fps')

# Save using tifffile (example)
tifffile.imwrite('slow_timelapse.tif', im)
```

### 3. Fast Sequence Acquisition
For high-speed imaging, stream frames directly using predefined configurations.

```python
# Stream a fast sequence for 30 seconds
fs.sequenceAcquisition(file_name='test', runtime=30, config='tr_40x_20fps')
```

### 4. Setting a Custom Region of Interest (ROI)
Define a centered hardware ROI on the camera sensor before starting an acquisition.

```python
import numpy as np

w = 1000
wmax = mmc.getImageWidth()

# Define centered ROI bounds [xmin, xmax, ymin, ymax]
roi = np.ceil(0.5 * np.array([wmax - w, wmax + w, wmax - w, wmax + w])).astype(int)

# Run fast sequence acquisition with the custom ROI
fs.sequenceAcquisition(file_name='test', runtime=30, config='rfp_100x_200fps', ROI=roi)
```

### 5. Stage Control (XY & Z)

```python
# Get current XY position
x1 = mmc.getXPosition()

# Move to absolute coordinates
mmc.setXYPosition(x1, 100)

# Get combined XY coordinates as a tuple
xy1 = mmc.getXYPosition()
mmc.setXYPosition(xy1[0], xy1[1])

# Get and set Z-axis position (focus)
z = mmc.getZPosition()
mmc.setZPosition(300)
```

### 6. System Maintenance & Metadata

```python
# Turn off the illumination lamp after an experiment
# Note: Keeps the microscope and peripheral power states alive
mmc.setConfig('lamp', 'off')

# Fetch all available hardware metadata tags
metadata_tags = mmc.getTags()

# Hot-reload the core module without restarting your Python session
from flashenscope.core import reload_core
reload_core()
```
