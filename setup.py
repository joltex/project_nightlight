from setuptools import setup, find_packages

setup(
    name='nightlight',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['adafruit-circuitpython-lis3dh',
                      'pillow'],
    entry_points={'console_scripts': ['convert = nightlight.converter:main']},
    url='https://github.com/joltex/project_nightlight',
    license='',
    author='',
    description=''
)