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

setup(
    name="social_auth",
    version="0.1.0",
    packages=["social_auth"],
    package_dir={"social_auth": "social_auth"},
    install_requires=install_requires,
    extras_require=social_core_extras_require,
    entry_points={
        "saleor.plugins": ["social_auth = social_auth.plugin:SocialAuthPlugin"]
    },
)
