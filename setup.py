from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(
    name='cloudshell_sandboxapi_wrapper',
    version='1.0.0',
    packages=['cloudshell_sandboxapi_wrapper'],
    url='http://www.quali.com',
    license='Apache 2.0',
    author='sadanand.s',
    author_email='sadanand.s@quali.com',
    description='Python wrapper for CloudShell Sandbox API',
    long_description=readme(),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=['requests']
)
