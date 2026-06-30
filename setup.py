from setuptools import find_packages, setup


HERMES_RUNTIME_REQUIREMENT = (
    "hermes-agent @ "
    "git+https://github.com/Bidzina83/hermes-agent.git"
    "@b13e2fd6948a59eeb59fe618914147d97a2ee90a"
)

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
    python_requires='>=3.11,<3.14',
    install_requires=[
        HERMES_RUNTIME_REQUIREMENT,
    ],
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
