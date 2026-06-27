from setuptools import setup, find_packages

setup(
    name="transit-ai",
    version="2.0.0",
    author="TRANSIT-AI Team",
    description="AI-enabled exoplanet detection from TESS light curves",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "transit-ai=src.pipeline.full_pipeline:cli_main",
            "transit-ai-demo=src.pipeline.full_pipeline:cli_demo",
            "transit-ai-validate=src.pipeline.validation_runner:cli_validate",
            "transit-ai-dashboard=app.streamlit_app:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Astronomy",
    ]
)
