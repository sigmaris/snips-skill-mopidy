from setuptools import setup

setup(
    name='snipsmopidy',
    version='1.0.1',
    description='Mopidy skill for Snips',
    author='The Als',
    url='https://github.com/sigmaris/snips-skill-mopidy',
    download_url='',
    license='MIT',
    install_requires=['python-mpd2', 'paho-mqtt'],
    test_suite="tests",
    keywords=['snips', 'mopidy'],
    packages=['snipsmopidy'],
    package_data={'snipsmopidy': ['Snipsspec']},
    include_package_data=True,
)
