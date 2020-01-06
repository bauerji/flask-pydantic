"""
Flask-Pydantic
-------------

This library provides port of Pydantic library to Flask.
It allows quick and easy-to-use way of data parsing and validation using python type
hints.
"""
from typing import Generator
from pathlib import Path
from setuptools import setup


REQUIREMENTS_PATH = Path(__file__).resolve().parent / "requirements" / "base.pip"


def get_install_requires(
    req_file: Path = REQUIREMENTS_PATH
) -> Generator[str, None, None]:
    with req_file.open("r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            yield line.strip()


setup(
    name="Flask-Pydantic",
    version="0.0.1",
    url="https://github.com/bauerji/flask_pydantic.git",
    license="MIT",
    author="Jiri Bauer",
    author_email="baueji@gmail.com",
    description="Flask extension for integration with Pydantic library",
    long_description=__doc__,
    py_modules=["flask_pydantic"],
    install_requires=list(get_install_requires()),
    python_requires=">=3.7",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
