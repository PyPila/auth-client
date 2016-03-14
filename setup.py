import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='amok-auth-client',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    license='GNU GPL v3',
    description=(
        'Simple client used in django porjects that need to use amok auth as'
        ' the authentiacation service.'
    ),
    long_description=README,
    author='Pawel Kucmus',
    author_email='pkucmus@gmail.com',
    install_requires=[
        'pyjwt==1.4.0',
        'restservice==0.2',
    ],
    dependency_links=[
        'git+https://github.com/PyPila/restservice.git#egg=restservice-0.2'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU GPL v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
