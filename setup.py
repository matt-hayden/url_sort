from setuptools import find_packages, setup

setup(name='UrlSort',
      version = "1.0.0b2",
      description='Recognize familiar filename patterns in URLs',
      url='https://github.com/matt-hayden/url_sort',
      maintainer="Matt Hayden (Valenceo, LTD.)",
      maintainer_email="github.com/matt-hayden",
      license='Unlicense',
      packages=find_packages(),
      entry_points = {
          'console_scripts': [
              'pastebin_mailbox_refresh=pastebin.cli:main',
              'urlsort=url_sort.cli:main',
              ],
      },
      install_requires = [ 'docopt', 'requests', 'tqdm' ],
      zip_safe=True
     )
