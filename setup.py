from setuptools import setup, find_packages

setup(
    name='project_maya',
    version='0.0.0',
    description='Project MAYA - packaged for CI',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
)
