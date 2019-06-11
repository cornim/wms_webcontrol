import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="warema-wms-controller",
    version="0.0.1",
    author="Dr. Cornelius Mund",
    author_email="cornelius.mund@gmail.com",
    description="A library to control a Warema WMS WebControl web server.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)