from setuptools import find_packages, setup


packages = find_packages(
    where="src",
    include=["project_maya", "project_maya.*"],
)

setup(
    name='project_maya',
    version='0.0.0',
    description='Project MAYA - packaged for CI',
    packages=packages,
    package_dir={"": "src"},
    include_package_data=False,
    package_data={'': ['plugin.yaml']},
    python_requires='>=3.10',
    # Optional extras for test/development workflows. Keep minimal and focused.
    extras_require={
        'test': [
            'pytest>=7.0',
            'pytest-mock',
            'jsonschema',
        ],
        'dev': [
            'pytest>=7.0',
            'pytest-mock',
            'jsonschema',
            'build',
        ],
        'migration': [
            'alembic>=1.13',
            'sqlalchemy>=2.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'maya=project_maya.cli:main',
        ],
    },
)
