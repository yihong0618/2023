from setuptools import find_packages, setup

setup(
    name="gh2023",
    author="yihong0618",
    author_email="zouzou0208@gmail.com",
    url="https://github.com/yihong0618/2023",
    license="MIT",
    version="2.3.0",
    description="My repo of my 2023",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["PyGithub", "requests", "pendulum"],
    entry_points={
        "console_scripts": ["gh2023 = github_daily.cli:main"],
    },
)
