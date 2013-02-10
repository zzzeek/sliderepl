from setuptools import setup, find_packages
import os

readme = os.path.join(os.path.dirname(__file__), 'README.rst')

requires = [
    'pygments',
]

try:
    import argparse
except ImportError:
    requires.append('argparse')

setup(name='sliderepl',
      version="1.1",
      description="Runs a python script as a series of slides for presentation.",
      long_description=open(readme).read(),
      classifiers=[
      'Development Status :: 4 - Beta',
      'Environment :: Console',
      'Intended Audience :: Developers',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: Implementation :: CPython',
      'Programming Language :: Python :: Implementation :: PyPy',
      ],
      keywords='',
      author='Jason Kirtland, Mike Bayer',
      author_email='mike@zzzcomputing.com',
      url='http://bitbucket.org/zzzeek/sliderepl',
      license='MIT',
      packages=find_packages('.', exclude=['examples*', 'test*']),
      include_package_data=True,
      #tests_require = ['nose >= 0.11'],
      #test_suite = "nose.collector",
      zip_safe=False,
      install_requires=requires,
      entry_points={
        'console_scripts': ['sliderepl = sliderepl.main:main'],
      }
)
