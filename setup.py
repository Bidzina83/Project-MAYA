from setuptools import setup, find_packages

# Discover packages both at repo root and under src/, and map any packages
# found under src/ to their filesystem location so setuptools can find them.
packages_root = find_packages(where='.')
packages_src = find_packages(where='src')
# Build package_dir mapping for packages located under src/.
# Only map a package from src/ if it does NOT already exist at the repo root.
package_dir = {}
for p in packages_src:
    if p not in packages_root:
        package_dir[p] = 'src/' + p.replace('.', '/')
# Combine discovered packages; root packages take precedence for on-disk layout.
packages = sorted(set(packages_root + packages_src))

setup(
    name='project_maya',
    version='0.0.0',
    description='Project MAYA - packaged for CI',
    packages=packages,
    package_dir=package_dir,
    include_package_data=True,
)
