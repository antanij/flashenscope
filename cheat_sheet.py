to install: go to .../GitHub/flashenscope
cd /d C:\Users\Flash\Documents\GitHub\flashenscope
conda activate <env_name>
pip install -e . --use-pep517

conda activate <env_name>
jupyter lab

import flashenscope as fs
fs.initalize()

# for slow time-lapse
im = fs.takePicture('tr_10x_20fps')
import tifffile as tiff
tiff.imwrite

# for fast imaging
fs.sequenceAcquisition(file_name='test', runtime=30, config='tr_40x_20fps')
# trying out different 
w = 1000

wmax = mmc.getImageWidth()
roi = np.ceil(1/2*[wmax-w wmax+w wmax-w wmax+w]) # defeining around the center-make sure this line works and replace if not
fs.sequenceAcquisition(file_name='test', runtime=30, config='rfp_100x_200fps',ROI=roi)

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