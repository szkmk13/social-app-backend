# socialapp

All and nothing


[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)

## Basic Commands
### Install requirements and migrate:
`pip install -r requirements/local.txt`

`python manage.py migarte`

### Start server
`python manage.py runserver`


### Setting Up Your Users

To create a **admin**, use this command:

  `python manage.py createsuperuser`


### Test command:
`pytest --cov-config .coveragerc --cov-report term --cov=socialapp`
### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

`coverage run -m pytest`

`coverage html`

`open htmlcov/index.html`


### Type checks

Running type checks with mypy:

    $ mypy socialapp
