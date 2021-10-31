from setuptools import setup
from setuptools import find_packages
import os

this_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(this_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="parasol",
    version="0.1",
    description="Control of Fenning Research Group outdoor testbed",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rishi Kumar",
    author_email="rek010@eng.ucsd.edu",
    download_url="https://github.com/fenning-research-group/parasol",
    license="MIT",
    install_requires=["numpy", "pyvisa", "asyncio", "pyyaml"],
    packages=find_packages(),
    package_data={"hardware": ["*.yaml"]},
    include_package_data=True,
    keywords=["materials", "science", "machine", "automation"],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    # entry_points={
    #     'console_scripts': [
    #         'meg = megnet.cli.meg:main',
    #     ]
    # }
)
