import os
import setuptools

DIR = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(DIR, "README.md"), "r") as f:
    long_description = f.read()

with open(os.path.join(DIR, "requirements.txt"), "r") as f:
    packages = f.read().split("\n")

setuptools.setup(
    name="dmi-forecast-edr",
    version="0.0.1",
    author="Oliver Lylloff",
    author_email="oliverlylloff@gmail.com",
    description="Python interface to DMI forecast data API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/1oly/dmi-forecast-edr",
    packages=setuptools.find_packages(),
    install_requires=packages,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    package_data={"": ["LICENSE", "requirements.txt"]},
    include_package_data=True,
)
