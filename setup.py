from setuptools import setup

setup(
    name="cli-tools",
    version="1.0",
    py_modules=[""],
    install_requires=["Click"],
    entry_points={
        "console_scripts": ["transclate=basic_cli:main"]
    },
)
