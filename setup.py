from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()


setup(
    name='jobnotify',
    version='0.1.0',
    description='Send notifications about new job listings.',
    long_description=readme,
    author='Matthew McKenna',
    author_email='mattheweb.mckenna@gmail.com',
    url='https://github.com/matthewmckenna/jobnotify',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'htmlcov')),
    entry_points={
        'console_scripts': [
            'jobnotify = jobnotify.jobnotify:main',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='jobnotify notify email slack job',
    include_package_data=True,
    install_requires=['slackclient>=1.0.5']
)
