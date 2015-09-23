from setuptools import setup, find_packages

setup(
    name='apprecommender',
    description="Package recommender for GNU packages",
    version='0.1',
    url='https://github.com/tassia/AppRecommender',
    author='Tassia Camoes Araujo',
    author_email='tassia@acaia.ca',
    license='GPLv3.txt',
    packages=find_packages(),
    test_suite="discover_tests",
    )
