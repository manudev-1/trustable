from setuptools import setup, find_packages

with open('requirements.txt', "r") as f:
    required = f.read().splitlines()

setup(
    name="Tustable",
    version="0.0",
    packages=find_packages(),
    install_requires = required,
    entry_points = {
      'console_scripts': [
            #! "cmd=module.file:start_function"
            "gmrs=console.gmrs:main",
            "profile=console.profiling:main"
      ]  
    },
    
    author="Manuele Barone",
    author_email="manuelebarone186@gmail.com",
    description="Is a Google Business Profile trustable",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)