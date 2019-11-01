from os import path

from setuptools import find_packages, setup


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "../README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="wagtail-grapple",
    version="0.4.2",
    packages=find_packages(include=["grapple"], exclude=["tests*"]),
    include_package_data=True,
    description="A django app that speeds up and simplifies implementing a GraphQL endoint!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/torchbox/wagtail-grapple",
    author="Nathan Horrigan",
    author_email="nathan.horrigan@torchbox.com",
    license="MIT",
    install_requires=[
        "wagtail>=2.5, <2.7",
        "Django>=2.2, <2.3",
        "graphene-django>=2.2.0" "graphql-core==2.2.1" "colorthief",
        "channels==1.1.8",
        "asgi_redis",
        "graphql_ws",
        "scour==0.37",
        "wagtail-headless-preview",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Wagtail",
        "Framework :: Wagtail :: 2",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
