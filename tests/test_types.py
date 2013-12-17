from datetime import datetime, timedelta, tzinfo
import unittest

#noinspection PyUnresolvedReferences
from nose.tools import assert_equal, assert_raises # you need it for tests in form of continuations
import pytz
import six

from flask_restful import types

# http://docs.python.org/library/datetime.html?highlight=datetime#datetime.tzinfo.fromutc
ZERO = timedelta(0)
HOUR = timedelta(hours=1)


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

def test_datetime_formatters():
    dates = [
        (datetime(2011, 1, 1), "Sat, 01 Jan 2011 00:00:00 -0000"),
        (datetime(2011, 1, 1, 23, 59, 59),
         "Sat, 01 Jan 2011 23:59:59 -0000"),
        (datetime(2011, 1, 1, 23, 59, 59, tzinfo=UTC()),
                  "Sat, 01 Jan 2011 23:59:59 -0000"),
        ]
    for date_obj, expected in dates:
        yield assert_equal, types.rfc822(date_obj), expected

def test_urls():
    urls = [
        'http://www.djangoproject.com/',
        'http://localhost/',
        'http://example.com/',
        'http://www.example.com/',
        'http://www.example.com:8000/test',
        'http://valid-with-hyphens.com/',
        'http://subdomain.example.com/',
        'http://200.8.9.10/',
        'http://200.8.9.10:8000/test',
        'http://valid-----hyphens.com/',
        'http://example.com?something=value',
        'http://example.com/index.php?something=value&another=value2',
        'http://foo:bar@example.com',
        'http://foo:@example.com',
        'http://foo:@2001:db8:85a3::8a2e:370:7334',
        'http://foo2:qd1%r@example.com',
        ]

    for value in urls:
        yield assert_equal, types.url(value), value

def check_bad_url_raises(value):
    try:
        types.url(value)
        assert False, "shouldn't get here"
    except ValueError as e:
        assert_equal(six.text_type(e), u"{0} is not a valid URL".format(value))

def test_bad_urls():
    values = [
        'foo',
        'http://',
        'http://example',
        'http://example.',
        'http://.com',
        'http://invalid-.com',
        'http://-invalid.com',
        'http://inv-.alid-.com',
        'http://inv-.-alid.com',
        'foo bar baz',
        u'foo \u2713',
        'http://@foo:bar@example.com',
        'http://:bar@example.com',
        'http://bar:bar:bar@example.com',
    ]

    for value in values:
        yield check_bad_url_raises, value

def test_bad_url_error_message():
    values = [
        'google.com',
        'domain.google.com',
        'kevin:pass@google.com/path?query',
        u'google.com/path?\u2713',
    ]

    for value in values:
        yield check_url_error_message, value

def check_url_error_message(value):
    try:
        types.url(value)
        assert False, u"types.url({0}) should raise an exception".format(value)
    except ValueError as e:
        assert_equal(six.text_type(e),
                      (u"{0} is not a valid URL. Did you mean: http://{0}".format(value)))


class TypesTestCase(unittest.TestCase):

    def test_boolean_false(self):
        assert_equal(types.boolean("False"), False)


    def test_boolean_true(self):
        assert_equal(types.boolean("true"), True)


    def test_boolean_upper_case(self):
        assert_equal(types.boolean("FaLSE"), False)


    def test_boolean(self):
        assert_equal(types.boolean("FaLSE"), False)


    def test_bad_boolean(self):
        assert_raises(ValueError, lambda: types.boolean("blah"))


    def test_date_later_than_1900(self):
        assert_equal(types.date("1900-01-01"), datetime(1900, 1, 1))


    def test_date_too_early(self):
        assert_raises(ValueError, lambda: types.date("0001-01-01"))


    def test_date_input_error(self):
        assert_raises(ValueError, lambda: types.date("2008-13-13"))

    def test_date_input(self):
        assert_equal(types.date("2008-08-01"), datetime(2008, 8, 1))

    def test_natual_negative(self):
        assert_raises(ValueError, lambda: types.natural(-1))

    def test_natural(self):
        assert_equal(3, types.natural(3))


    def test_natual_string(self):
        assert_raises(ValueError, lambda: types.natural('foo'))

    def test_positive(self):
        assert_equal(1, types.positive(1))
        assert_equal(10000, types.positive(10000))

    def test_positive_zero(self):
        assert_raises(ValueError, lambda: types.positive(0))

    def test_positive_negative_input(self):
        assert_raises(ValueError, lambda: types.positive(-1))


def test_isointerval():
    intervals = [
        (
            # Full precision with explicit UTC.
            "2013-01-01T12:30:00Z/P1Y2M3DT4H5M6S",
            (
                datetime(2013, 1, 1, 12, 30, 0, tzinfo=pytz.UTC),
                datetime(2014, 3, 5, 16, 35, 6, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Full precision with alternate UTC indication
            "2013-01-01T12:30+00:00/P2D",
            (
                datetime(2013, 1, 1, 12, 30, 0, tzinfo=pytz.UTC),
                datetime(2013, 1, 3, 12, 30, 0, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Implicit UTC with time
            "2013-01-01T15:00/P1M",
            (
                datetime(2013, 1, 1, 15, 0, 0, tzinfo=pytz.UTC),
                datetime(2013, 1, 31, 15, 0, 0, tzinfo=pytz.UTC),
            ),
        ),
        (
            # TZ conversion
            "2013-01-01T17:00-05:00/P2W",
            (
                datetime(2013, 1, 1, 22, 0, 0, tzinfo=pytz.UTC),
                datetime(2013, 1, 15, 22, 0, 0, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Date upgrade to midnight-midnight period
            "2013-01-01/P3D",
            (
                datetime(2013, 1, 1, 0, 0, 0, tzinfo=pytz.UTC),
                datetime(2013, 1, 4, 0, 0, 0, 0, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Start/end with UTC
            "2013-01-01T12:00:00Z/2013-02-01T12:00:00Z",
            (
                datetime(2013, 1, 1, 12, 0, 0, tzinfo=pytz.UTC),
                datetime(2013, 2, 1, 12, 0, 0, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Start/end with time upgrade
            "2013-01-01/2013-06-30",
            (
                datetime(2013, 1, 1, tzinfo=pytz.UTC),
                datetime(2013, 6, 30, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Start/end with TZ conversion
            "2013-02-17T12:00:00-07:00/2013-02-28T15:00:00-07:00",
            (
                datetime(2013, 2, 17, 19, 0, 0, tzinfo=pytz.UTC),
                datetime(2013, 2, 28, 22, 0, 0, tzinfo=pytz.UTC),
            ),
        ),
        # Resolution expansion for single date(time)
        (
            # Second with UTC
            "2013-01-01T12:30:45Z",
            (
                datetime(2013, 1, 1, 12, 30, 45, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 12, 30, 46, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Second with tz conversion
            "2013-01-01T12:30:45+02:00",
            (
                datetime(2013, 1, 1, 10, 30, 45, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 10, 30, 46, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Second with implicit UTC
            "2013-01-01T12:30:45",
            (
                datetime(2013, 1, 1, 12, 30, 45, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 12, 30, 46, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Minute with UTC
            "2013-01-01T12:30+00:00",
            (
                datetime(2013, 1, 1, 12, 30, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 12, 31, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Minute with conversion
            "2013-01-01T12:30+04:00",
            (
                datetime(2013, 1, 1, 8, 30, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 8, 31, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Minute with implicit UTC
            "2013-01-01T12:30",
            (
                datetime(2013, 1, 1, 12, 30, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 12, 31, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Hour, explicit UTC
            "2013-01-01T12Z",
            (
                datetime(2013, 1, 1, 12, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 13, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Hour with offset
            "2013-01-01T12-07:00",
            (
                datetime(2013, 1, 1, 19, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 20, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Hour with implicit UTC
            "2013-01-01T12",
            (
                datetime(2013, 1, 1, 12, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 13, tzinfo=pytz.UTC),
            ),
        ),
        (
            # Interval with trailing zero fractional seconds should
            # be accepted.
            "2013-01-01T12:00:00.0/2013-01-01T12:30:00.000000",
            (
                datetime(2013, 1, 1, 12, tzinfo=pytz.UTC),
                datetime(2013, 1, 1, 12, 30, tzinfo=pytz.UTC),
            ),
        ),
    ]

    for value, expected in intervals:
        yield assert_equal, types.iso8601interval(value), expected


def test_isointerval_too_early():
    with assert_raises(ValueError) as cm:
        types.iso8601interval('1847-03-03/1922-08-02')

    error = cm.exception
    assert_equal(
        error.message,
        "Invalid argument: 1847-03-03/1922-08-02. The year must be >= 2000.",
    )


def test_invalid_isointerval_error():
    with assert_raises(ValueError) as cm:
        types.iso8601interval('2013-01-01/blah')

    error = cm.exception
    assert_equal(
        error.message,
        "Invalid argument: 2013-01-01/blah. argument must be a valid ISO8601 "
        "date/time interval.",
    )


def test_no_subsecond_isointerval():
    with assert_raises(ValueError) as cm:
        types.iso8601interval('2013-01-01T12:00:00.1')

    error = cm.exception
    assert_equal(
        error.message,
        "Invalid argument: 2013-01-01T12:00:00.1. The smallest supported "
        "resolution for datetimes is one second.",
    )


def test_bad_isointervals():
    bad_intervals = [
        '2013-01T14:',
        '',
        'asdf',
        '01/01/2013',
    ]

    for bad_interval in bad_intervals:
        yield (
            assert_raises,
            ValueError,
            types.iso8601interval,
            bad_interval,
        )

if __name__ == '__main__':
    unittest.main()
