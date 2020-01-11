import os.path

import setuptools

README_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                           'README.md')
with open(README_PATH) as f:
    LONG_DESCRIPTION = f.read()

setuptools.setup(
    name='pysrbup',
    version='0.1.0a1',
    description='Secure distributed backups',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    python_requires='==3.*,>=3.6.0',
    project_urls={
        'homepage': 'https://github.com/dor98/keydope',
        'repository': 'https://github.com/dor98/keydope'
    },
    author='dor98',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows :: Windows 10'
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='backups encryption compression',
    packages=setuptools.find_packages(exclude=['tests']),
    package_data={},
    install_requires=[
        'cryptography==2.*,>=2.8.0', 'grpcio==1.*,>=1.26.0',
        'grpcio-tools==1.*,>=1.26.0'
    ],
    entry_points={
        'console_scripts': [
            'pysrbup-client = pysrbup.client:main',
            'pysrbup-server = pysrbup.server:main',
        ]
    },
    extras_require={
        'dev': [
            'coverage==4.*,>=4.4.2', 'isort==4.*,>=4.3.0', 'jedi==0.*,>=0.15.2',
            'pycodestyle==2.*,>=2.5.0', 'pydocstyle==5.*,>=5.0.0',
            'pylint==2.*,>=2.4.0', 'pytest==5.*,>=5.3.0',
            'pytest-cov==2.*,>=2.6.0', 'pytype==2020.*,>=2020.0.0',
            'tox==3.*,>=3.14.0'
        ]
    },
)
