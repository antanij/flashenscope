to install: go to .../GitHub/flashenscope
conda activate <env_name>
pip install -e . --use-pep517

conda activate <env_name>
jupyter lab

import flashenscope.functions as fs
fs.initalize()

# for slow time-lapse
im = fs.takePicture('tr_10x_20fps')
import tifffile as tiff
tiff.imwrite

# for fast imaging
fs.sequenceAcquisition('tr_10x_20fps', duration_s=30, fps=100, save_path='movie.tif')

# reloading core
from flashenscope.core import reload_core
reload_core()


x1 = mmc.getXPosition()
mmc.setXYPosition(x1,100)
xy1 = mmc.getXYPosition()
mmc.setXYPosition(xy1[0],xy1[1])

z = mmc.getZPosition()
mmc.setZPosition(0)

mmc.setConfig('lamp','off')

mmc.getTags # gets all metadata