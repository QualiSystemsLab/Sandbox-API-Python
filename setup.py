from typing import List

from setuptools import find_packages, setup


def read_file(file_name: str) -> str:
    with open(file_name) as f:
        content = f.read().strip()
    return content


def lines_from_file(file_name: str) -> List[str]:
    with open(file_name) as f:
        lines = f.read().splitlines()
    return lines


setup(
    name="cloudshell_sandboxapi_wrapper",
    description="Python client for CloudShell Sandbox REST api - consume sandboxes via CI",
    keywords=["cloudshell", "sandbox", "api", "rest", "CI"],
    url="https://github.com/QualiSystemsLab/Sandbox-API-Python",
    author="sadanand.s",
    author_email="sadanand.s@quali.com",
    license="Apache 2.0",
    packages=find_packages(),
    version=read_file("version.txt"),
    long_description=read_file("README.MD"),
    long_description_content_type='text/markdown',
    install_requires=lines_from_file("requirements.txt"),
    test_requires=lines_from_file("test-requirements.txt"),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
