from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='piscreen',
    version='0.1.0',
    description='PiScreen package, to display remote images on a raspberry Pi 3.5" LCD',
    long_description=readme,
    author='Jordi Vea i Barbany',
    author_email='jordi.vea@gmail.com',
    url='https://github.com/jordivea/piscreen',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'tmp'))
)
