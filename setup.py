from setuptools import find_packages, setup

setup(name='UrlList',
      version = "0.0.1",
      description='Recognize familiar filename patterns in URI links',
      url='https://github.com/matt-hayden/url_list',
      maintainer="Matt Hayden (Valenceo, LTD.)",
      maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(),
      entry_points = {
          'console_scripts': [
              'urlsort=url_list.cli:main',
              ]
      },
      zip_safe=True
     )
