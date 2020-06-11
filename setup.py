"""
Flask-Pydantic
-------------

This library provides port of Pydantic library to Flask.
It allows quick and easy-to-use way of data parsing and validation using python type
hints.
"""
import re
from pathlib import Path
from setuptools import setup
from typing import Generator


CURRENT_FOLDER = Path(__file__).resolve().parent
REQUIREMENTS_PATH = CURRENT_FOLDER / "requirements" / "base.pip"
VERSION_FILE_PATH = CURRENT_FOLDER / "flask_pydantic" / "version.py"
VERSION_REGEX = r"^__version__ = [\"|\']([0-9\.a-z]+)[\"|\']"
README = (CURRENT_FOLDER / "README.md").read_text()


def get_install_requires(
    req_file: Path = REQUIREMENTS_PATH,
) -> Generator[str, None, None]:
    with req_file.open("r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            yield line.strip()


def find_version(file_path: Path = VERSION_FILE_PATH) -> str:
    file_content = file_path.open("r").read()
    version_match = re.search(VERSION_REGEX, file_content, re.M)

    if version_match:
        return version_match.group(1)
    raise RuntimeError(f"Unable to find version string in {file_path}")


setup(
    name="Flask-Pydantic",
    version=find_version(),
    url="https://github.com/bauerji/flask_pydantic.git",
    license="MIT",
    author="Jiri Bauer",
    author_email="baueji@gmail.com",
    description="Flask extension for integration with Pydantic library",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["flask_pydantic"],
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
