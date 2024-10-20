import random
from dateutil.relativedelta import relativedelta


def get_random_date(start_date, end_date):
    """
    Returns a random date between start_date and end_date.

    :param start_date: The earliest possible date (inclusive)
    :param end_date: The latest possible date (inclusive)
    :return: A random date between start_date and end_date
    """
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + relativedelta(days=random_days)
