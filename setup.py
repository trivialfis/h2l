from setuptools import setup, find_packages
import os
from H2L.configuration import dependencies as deps

build_dependencies = deps.build_time(deps.H2L_DEPENDENCIES)
dependencies_list = [dep[0] + '>=' + dep[1] for dep in build_dependencies]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='H2L',
    version='0.1',
    author='GamingJyun',
    author_email='gaming-jyun@outlook.com',
    license='GPL-v3',
    packages=find_packages(),
    install_requires=dependencies_list,
    include_package_data=True,
    package_data={'H2L': ['models/character_cnn_architure.json',
                          'models/character_cnn_weights.hdf5',
                          'models/character_res_architure.json',
                          'models/character_res_weights.hdf5',
                          'models/characters_map']},
    tests_require=['pytest'],
    data_files=[('share/applications', ['resource/h2l.desktop']),
                ('share/pixmaps', ['resource/h2l.png'])],
    scripts=['h2l', 'h2l_commands'],
    description=("Experment project for recognizing math equations."),
    long_description=read('README.org'),
    project_urls={
        'Source Code': 'https://github.com/trivialfis/H2L'
    }
)
