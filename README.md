django-balanced
===============

[![Build Status](https://secure.travis-ci.org/balanced/django-balanced.png)](http://travis-ci.org/dmpayton/django-balanced)
[![Coverage Status](https://coveralls.io/repos/balanced/django-balanced/badge.png?branch=develop)](https://coveralls.io/r/balanced/django-balanced)
[![Downloads](https://pypip.in/d/django-balanced/badge.png)](https://pypi.python.org/pypi/django-balanced)

Django integration for [Balanced Payments](https://www.balancedpayments.com/).

* **Version**: 0.1.10
* **License**: BSD

This version is compatible with the
[Balanced API v1.0](https://docs.balancedpayments.com/1.0/overview/) using
[balanced-python 0.11.15](https://pypi.python.org/pypi/balanced/0.11.15).

How to send ACH payments in 10 minutes
--------------------------------------

1. Visit www.balancedpayments.com and get yourself an API key

2. `pip install django-balanced`

3. Edit your `settings.py` and add the API key like so:

    ```
    import os

    BALANCED = {
        'API_KEY': os.environ.get('BALANCED_API_KEY'),
    }
    ```

4. Add `django_balanced` to your `INSTALLED_APPS` in `settings.py`

    ```
    INSTALLED_APPS = (
       ...
       'django.contrib.admin',  # if you want to use the admin interface
       'django_balanced',
       ...
    )
    ```

5. Run `BALANCED_API_KEY=YOUR_API_KEY django-admin.py syncdb`

6. Run `BALANCED_API_KEY=YOUR_API_KEY python manage.py runserver`

7. Visit `http://127.0.0.1:8000/admin` and pay some people!

Testing
-------

Continuous integration provided by [Travis CI](https://travis-ci.org/).

### Running the tests

1. Install all requirements:

    ```
    $ pip install Django -r requirements.txt -r test-requirements.txt
    ```

2. Run the tests:

    ```
    $ ./run-tests.py

    ...

    =============== 2 passed, 17 skipped in 15.95 seconds ===============
    ```

### Testing with Tox

For quickly testing against different Django versions, we use
[Tox](http://tox.readthedocs.org/).

```
$ tox

...

_______________ summary _______________
  py27-django17: commands succeeded
  py27-django16: commands succeeded
  py27-django15: commands succeeded
  py27-django14: commands succeeded
  congratulations :)
```
