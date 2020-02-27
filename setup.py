from setuptools import setup, find_packages


def find_version(path):
    import re

    s = open(path, "rt").read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", s, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Version not found")


setup(
    name="qcmr",
    version=find_version("qcmr/__init__.py"),
    author="Nick Hand",
    maintainer="Nick Hand",
    maintainer_email="nick.hand@phila.gov",
    description="Digitizing the City of Philadelphia's Quarterly City Manager's Report",
    license="MIT",
    packages=find_packages(),
)
