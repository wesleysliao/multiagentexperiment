import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="multiagentexperiment",
    version="0.0.1",
    author="Wesley Liao",
    author_email="wesliao@iu.edu",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wesleysliao/multiagentexperiment",
    project_urls={
        "Bug Tracker": "https://github.com/wesleysliao/multiagentexperiment/issues",
        "Documentation": "https://multiagentexperiment.docsforge.com",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU GPLv3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)