from setuptools import find_packages, setup

setup(
    name='data_wrangler',
    packages=find_packages(include=['data_wrangler']),
    version='0.0.1',
    description='A collection of python tools and libraries for computational social science research',
    author='Sylvan Zheng <saz310@nyu.edu',
    license='MIT',
    install_requires=['openai']
)