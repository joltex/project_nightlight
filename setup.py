from setuptools import setup, find_packages

setup(
    name='project_nightlight',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['pillow'],
    # entry_points={'console_scripts': ['convert = project_nightlight.converter:main']},
    url='https://github.com/joltex/project_nightlight',
    license='',
    author='',
    description=''
)