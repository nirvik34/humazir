from setuptools import setup, find_packages

setup(
    name="humanizr",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer",
        "rich",
        "pyyaml",
        "requests",
        "python-docx",
        "PyMuPDF"
    ],
    entry_points={
        "console_scripts": [
            "humanizr=humanizr.cli:run"
        ]
    }
)