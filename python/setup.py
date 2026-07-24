from setuptools import setup, find_packages

setup(
    name='visual-regression-engine',
    version='1.0.0',
    description='Python PIL-based visual regression comparison engine',
    author='Kishan Borad',
    packages=find_packages(),
    install_requires=['Pillow>=10.0.0'],
    entry_points={
        'console_scripts': [
            'vr-compare=diff_engine:main',
            'vr-batch=batch_compare:main',
        ],
    },
    python_requires='>=3.9',
)
