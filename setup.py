from setuptools import find_packages, setup

setup(
    name='squidtools',
    packages=find_packages(),
    version='0.0.11',
    description='A collection of python tools and libraries for computational social science research',
    author='Sylvan Zheng <saz310@nyu.edu>',
    license='MIT',
    install_requires=['openai', 'bs4', 'lxml']
)
