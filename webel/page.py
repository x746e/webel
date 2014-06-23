import re
from urlparse import urlunparse, urlparse
from webel.driver import get_driver
from selenium.webdriver.support.wait import WebDriverWait


class Page(object):

    url = None
    # TODO: Params, parametrized URLs.  E.g.:
    # class CoursePage(Page):
    #     url = '/courses/#/course/{slug}'
    #
    # page = CoursePage(slug='performance-and-identity')

    def __init__(self, load=None, assert_is_on_page=None, timeout=10, **kwargs):
        if load is True and assert_is_on_page is True:
            raise TypeError("That's not valid to set `load` and "
                            "`assert_is_assert_is_on_page` to True at the same time.")

        if (assert_is_on_page or load) and self.url is None:
            raise TypeError("Page need `self.url` for assert_is_on_page or load.")

        self.check_kwargs(kwargs)

        if self.url is not None and kwargs:
            self.url = self.url.format(**kwargs)

        self.driver = get_driver()

        if assert_is_on_page or (
                not load and assert_is_on_page is None and self.url is not None
                and not '{' in self.url):
            self._assert_is_on_page(timeout=timeout)

        if load:
            self.load()

    @property
    def webelement(self):
        return self.driver

    def load(self):
        self.driver.get(self.url)

    def _assert_is_on_page(self, timeout=10):
        WebDriverWait(None, timeout).until(
            lambda _driver: self._is_on_the_page(),
            message='Timeout while waiting for URL to become %r' % self.url,
        )
        assert self._is_on_the_page()

    def _is_on_the_page(self):
        return self._clean_url(self.driver.current_url) == self.url

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
            err_str += 'Superfluous arguments to %s: %r.' % (
                self.__class__.__name__, excess_vars)
        if absent_vars:
            err_str.append('Absent arguments to %s: %r.' % (
                self.__class__.__name__, absent_vars))
        if excess_vars or absent_vars:
            raise TypeError(' '.join(err_str))

