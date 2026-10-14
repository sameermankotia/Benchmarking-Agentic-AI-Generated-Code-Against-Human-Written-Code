#!/usr/bin/env python3
"""
Setup script for Django Framework.
"""

from setuptools import setup, find_packages

setup(
    name="djangoframework",
    version="0.1.0",
    description="A Django-like WSGI framework implementation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Django Framework",
    author_email="django@example.com",
    url="https://github.com/example/djangoframework",
    packages=find_packages(),
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov"],
    },
)
