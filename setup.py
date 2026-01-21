from setuptools import setup, find_packages

setup(
    name="healthcare-supply-chain-etl",
    version="1.0.0",
    description="Healthcare Supply Chain Analytics Data Pipeline",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.1.0",
        "supabase>=2.0.0",
        "streamlit>=1.30.0",
        "apache-airflow>=2.8.0",
        "great-expectations>=0.18.0",
    ],
    python_requires=">=3.10",
)