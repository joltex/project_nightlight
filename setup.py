from setuptools import setup, find_packages

setup(
    name='nightlight',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'adafruit-blinka==5.9.2',
        'adafruit-circuitpython-lis3dh',
        'matplotlib',
        'noise',
        'numpy',
        'pillow',
        'youtube-dl'
    ],
    entry_points={'console_scripts': ['nightlight=nightlight.cli:main']},
    url='https://github.com/joltex/project_nightlight',
    license='',
    author='',
    description=''
)
