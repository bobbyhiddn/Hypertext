#!/usr/bin/env python3
"""Setup script for hypertext-tools package."""

from setuptools import setup, find_packages

setup(
    name="hypertext-tools",
    version="0.1.0",
    description="Biblical word-study trading card game toolkit",
    author="Hypertext Project",
    packages=find_packages(),
    package_data={
        "hypertext": ["templates/*", "templates/**/*"],
    },
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "Pillow>=10.0.0",
        "PyYAML>=6.0",
        "google-genai>=0.3.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": ["jsonschema", "markdown"],
    },
    entry_points={
        "console_scripts": [
            "hypertext=hypertext.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
