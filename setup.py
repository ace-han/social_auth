from setuptools import setup

install_requires = []

setup(
    name="social_auth",
    version="0.1.0",
    packages=["social_auth"],
    package_dir={"social_auth": "social_auth"},
    install_requires=install_requires,
    entry_points={
        "saleor.plugins": ["social_auth = social_auth.plugin:SocialAuthPlugin"]
    },
)
