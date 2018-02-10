from setuptools import find_packages, setup

setup(name='UrlSort',
      version = "0.0.1",
      description='Recognize familiar filename patterns in URLs',
      url='https://github.com/matt-hayden/url_sort',
      maintainer="Matt Hayden (Valenceo, LTD.)",
      maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(),
      entry_points = {
          'console_scripts': [
              'urlsort=url_sort.cli:main',
              ]
      },
      zip_safe=True
     )
