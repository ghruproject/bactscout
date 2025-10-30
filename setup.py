from setuptools import find_packages, setup

setup(
    name="bactscout",
    version="1.1.2",
    packages=find_packages(),
    entry_points={"console_scripts": ["bactscout = bactscout:app"]},
    install_requires=[
        "fastp>=1.0.1,<2",
        "sylph>=0.8.1,<0.9",
        "typer>=0.19.2,<0.20",
        "rich>=14.1.0,<15",
        "pyaml>=25.7.0,<26",
        "psutil>=7.1.0,<8",
        "stringmlst>=0.6.3,<0.7",
        "requests>=2.32.5,<3",
    ],
)
