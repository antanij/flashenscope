to install: got to .../GitHub/flashenscope
conda activate <env_name>
pip install -e . --use-pep517

conda activate <env_name>
jupyter lab

import flashenscope.functions as fs
fs.initalize()
fs.takePicture('tr_10x_20fps')
fs.sequenceAcquisition('tr_10x_20fps', duration_s=30, fps=100, save_path='movie.tif')


from flashenscope.core import reload_core
reload_core()


x = mmc.getXPosition()
mmc.setZPosition(0)