from setuptools import setup

install_requires = [
    'social-auth-app-django',
]

# copy from `python-social-auth` social-core/setup.py
social_core_extras_require={
    'openidconnect': ['python-jose>=3.0.0'],
    'saml': ['python3-saml>=1.2.1'],
    'azuread': ['cryptography>=2.1.1'],
    'all': [
        'python-jose>=3.0.0', 
        'python3-saml>=1.2.1', 
        'cryptography>=2.1.1',
    ]
}

README = 'file README.md'
with open("README.md") as readme:
    README = readme.read()

setup(
    name="saleor-social-auth",
    version="0.3.0",
    description="Social auth plugin (wx, alipay & etc.) for Saleor",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/ace-han/social_auth",
    author="Ace Han",
    author_email="ace.jl.han@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    packages=["social_auth"],
    package_dir={"social_auth": "social_auth"},
    install_requires=install_requires,
    extras_require=social_core_extras_require,
    zip_safe=True,
    entry_points={
        "saleor.plugins": ["social_auth = social_auth.plugin:SocialAuthPlugin"]
    },
)
