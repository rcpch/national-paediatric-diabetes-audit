---
title: Manual development setup
reviewers: Dr Marcus Baw, Dr Simon Chapman
---

If you prefer to set up a development environment manually, here are the steps. **Please note that we do not provide support for developers using a bespoke setup, only the Docker development environment is supported.**

This manual approach will require you to have much more familiarity with configuring PostgresQL, Django, and Python to achieve your aims, and is not for beginners.

## Install PostgreSQL and create the database with the correct credentials

You will need the [Postgresql](https://www.postgresql.org/) database, which can be installed natively on your development machine, or (recommended) can be installed using Docker.

Using the command below will create a development database with credentials that match those in our `envs/env-template` file.
You will need Docker to be installed on your local machine. (Please search the web for instructions for installation on your operating system and setup)

```console
docker run --name npda12postgres \
    -e POSTGRES_USER=npdauser \
    -e POSTGRES_PASSWORD=npda \
    -e POSTGRES_DB=npdadb \
    -p 5432:5432 \
    -d postgres
```

## Install the correct Python version

If you don't have Python installed already, you will need it. To avoid specifying a specific Python version for the project here in the documentation, please check the `Dockerfile` in the project root for the version of Python that is currently being used.

We recommend the use of a tool such as [pyenv](https://github.com/pyenv/pyenv) to assist with managing multiple Python versions and their accompanying virtualenvs.

```console
pyenv install <PYTHON_VERSION>
```

> On some platforms, you will get errors at build-time, which indicates you need to install some dependencies which are required for building the Python binaries locally. Rather than listing these here, where they may become out of date, please refer to the [pyenv wiki](https://github.com/pyenv/pyenv/wiki) which covers this in detail.

Then create a virtual environment:

```console
pyenv virtualenv <PYTHON_VERSION> rcpch-audit-engine
```

Clone the repository and `cd` into the directory:

```console
git clone https://github.com/rcpch/national-paediatric-diabetes-audit.git
cd npda
```

Then install all the requirements. Note you can't do this without PostgreSQL already installed first.

```console
pip install -r requirements/development-requirements.txt
```

## Set and initialize the environment variables

You will need to set the environment variables for your local development, using the `envs/env-template` file as a starting point. **This file should not be committed to the repository**. You can use real values for the environment variables in this file.

```console
source envs/.env
```

!!! danger
The included example environment variables are not secure and must never be used in production.

## Prepare the database for use

```console
python manage.py migrate
```

## Create superuser to enable logging into admin section

```console
python manage.py createsuperuser
```

Then follow the command line prompts to create the first user. Createsuperuser is a Django base feature but there are some custom fields which are mandatory. These include:

- `role`: The options are: `1 - Coordinator, 2 - Editor, 3 - Reader, 4 - RCPCH Audit Team`. If the integer selected in 1-3 (ie a role within the NPDA site) KCH is automatically allocated. If it is an RCPCH user, `is_rcpch_staff` is automatically set to true, as is `is_rcpch_audit_team_member`

- `is_rcpch_audit_team_member`: `True|False`.

Further users can subsequently be created in the Admin UI

## Running the server

Navigate to the NPDA outer folder and run the server:

```console
python manage.py runserver
```

## Seeding the Database

Migrations will seed the database with the following:

- Organisations
- Trusts
- ICBs (including boundaries)
- NHS England regions (including boundaries)
- Countries (including boundaries)

By running the migrations there database will therefore be ready to accept new users and children.

In development, it is often necessary to have some seeded children across multiple organisations to test functionality, so in addition there are 2 further seed commands:

This will seed with the defaults documented above.

## Running the tests locally

We have used the coverage package to test our models. It is already in our development requirements, but if you don't have it installed, install it with `pip install coverage`

Run all the tests

```console
coverage run manage.py test
coverage html
```

If the `htmlcov/index.html` is opened in the browser, gaps in outstanding testing of the models can be found.
