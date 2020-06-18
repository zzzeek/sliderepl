import os

from setuptools import find_packages
from setuptools import setup


readme = os.path.join(os.path.dirname(__file__), "README.rst")

requires = [
    "pygments",
]


setup(
    name="sliderepl",
    version="1.1",
    description="Runs a python script as a series of slides for presentation.",
    long_description=open(readme).read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">= 3.6",
    keywords="",
    author="Jason Kirtland, Mike Bayer",
    author_email="mike@zzzcomputing.com",
    url="http://github.com/zzzeek/sliderepl",
    license="MIT",
    packages=find_packages(".", exclude=["examples*", "test*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points={"console_scripts": ["sliderepl = sliderepl.main:main"]},
)
