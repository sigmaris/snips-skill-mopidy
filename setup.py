from setuptools import setup

setup(
    name='snipsmopidy',
    version='1.0.0',
    description='Snips skill to control Mopidy',
    author='pau.fabregat-pappaterra@snips.ai',
    url='https://github.com/snipsco-forks/snips-skill-mopidy',
    download_url='',
    license='MIT',
    install_requires=['mopidy', 'requests'],
    test_suite="tests",
    keywords=['snips', 'mopidy'],
    packages=['snipsmopidy'],
    package_data={'snipsmopidy': ['Snipsspec']},
    include_package_data=True,
)
