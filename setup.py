"""
Setup script for BSTI Nessus to Plextrac Converter.
"""
import os
import re
from setuptools import setup, find_packages


def read(filename):
    """Read file contents."""
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


def get_version():
    """Get version from __init__.py."""
    init_py = read('bsti_nessus/__init__.py')
    return re.search(r"__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_requirements():
    """Get requirements from requirements.txt."""
    requirements = []
    with open('bsti_nessus/requirements.txt') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)
    return requirements


setup(
    name="bsti-nessus",
    version=get_version(),
    description="BSTI Nessus to Plextrac Converter",
    long_description=read('bsti_nessus/README.md'),
    long_description_content_type="text/markdown",
    author="BSTI Team",
    author_email="info@bsti.com",
    url="https://github.com/bsti-security/bsti-nessus",
    packages=find_packages(),
    package_data={
        "bsti_nessus": [
            "README.md",
            "requirements.txt",
        ],
    },
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "bsti-nessus=bsti_nessus.core.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    keywords="security, vulnerability, assessment, plextrac, nessus",
    zip_safe=False,
) 