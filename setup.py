from setuptools import setup

setup(
    name='webel',
    version='0.1.0',
    author='Kirill Spitsin',
    author_email='tn@0x746e.org.ua',
    packages=['webel'],
    license='LICENSE',
    description='Helpers for doing web-testing with Webdriver',
    long_description=open('README.rst').read(),
    install_requires=['selenium'],
)
