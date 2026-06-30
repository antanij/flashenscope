from setuptools import setup, find_packages

setup(
    name='flashenscope',
    version='0.1',
    description='Flashenscope Package for Microscopy Control',
    author='antanij',
    author_email='jyot.antani@yale.edu',
    url='https://antanij.netlify.app/',
    packages=find_packages(),
    install_requires=[
        'pymmcore_plus',
        'numpy',
        'matplotlib',
        'imageio',
        'opencv-python',
        'screeninfo',        
    ],
)
