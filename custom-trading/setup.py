#!/usr/bin/env python3
"""
DEGIRO Trading API Setup
Standalone trading API that uses degiro-connector as external dependency
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="degiro-trading-api",
    version="2.1.0",
    author="Sebastian Mertens",
    description="Production-ready FastAPI server for automated DEGIRO trading",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "degiro-trading-api=api.main:run_server",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.env.example"],
    },
)