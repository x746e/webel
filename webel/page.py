import re
from urlparse import urlunparse, urlparse
import time
from webel.driver import get_driver
from webel.exceptions import TimeoutException


class Page(object):

    url = None

    def __init__(self, load=None, assert_is_on_page=None, timeout=10, **kwargs):  # XXX: assert_is_on_page -> wait_for_load?
        if load is True and assert_is_on_page is True:
            raise TypeError("That's not valid to set `load` and "
                            "`assert_is_assert_is_on_page` to True at the same time.")

        if (assert_is_on_page or load) and self.url is None:
            raise TypeError("Page need `self.url` for assert_is_on_page or load.")

        self.params = {}

        self.check_kwargs(kwargs)

        if self.url is not None and kwargs:
            self.url = self.url.format(**kwargs)
            self.params.update(kwargs)

        self.driver = get_driver()

        if assert_is_on_page or (
                not load and assert_is_on_page is None and self.url is not None):
            self._assert_is_on_page(timeout=timeout)

        if load:
            self.load()

    @property
    def webelement(self):
        return self.driver

    def load(self):
        self.driver.get(self.url)

    def _assert_is_on_page(self, timeout=20):
        # Convert URI template into regex (not every URI template, only very
        # basic ones).
        regex = r'^%s$' % re.sub(r'{(\w+)}', r'(?P<\1>[\w-]+)', self.url)

        cleaned_url = 'UNDEFINED'
        start = time.time()
        while time.time() - start < timeout:
            cleaned_url = self._clean_url(self.driver.current_url)
            if '{' in self.url:
                match = re.match(regex, cleaned_url)
                if match:
                    self.params.update(match.groupdict())
                    return
            else:
                if cleaned_url == self.url:
                    return
            time.sleep(.1)

        raise TimeoutException(
            'Timeout while waiting for URL to become %r.  Current URL is: %r.' % (
                self.url, cleaned_url))

    @staticmethod
    def _clean_url(url):
        parsed = list(urlparse(url))
        parsed[4] = ''  # Remove query.
        return urlunparse(parsed)

    def check_kwargs(self, kwargs):
        url_params = re.findall(r'{(\w+)}', self.__class__.url) if self.url else []
        excess_vars = set(kwargs.keys()) - set(url_params)
        absent_vars = None  #set(url_params) - set(kwargs.keys())
        err_str = []
        if excess_vars:
            err_str.append('Superfluous arguments to %s: %r.' % (
                self.__class__.__name__, excess_vars))
        if absent_vars:
            err_str.append('Absent arguments to %s: %r.' % (
                self.__class__.__name__, absent_vars))
        if excess_vars or absent_vars:
            raise TypeError(' '.join(err_str))

