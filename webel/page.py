from urlparse import urlunparse, urlparse
from webel.driver import get_driver


class Page(object):

    url = None

    def __init__(self, load=None, assert_is_on_page=None):
        if load is True and assert_is_on_page is True:
            raise TypeError("That's not valid to set `load` and "
                            "`assert_is_assert_is_on_page` to True at the same time.")

        if (assert_is_on_page or load) and self.url is None:
            raise TypeError("Page need `self.url` for assert_is_on_page or load.")

        self.driver = get_driver()

        if assert_is_on_page:
            assert self._is_on_the_page()

        if load:
            self.load()

    @property
    def webelement(self):
        return self.driver

    def load(self):
        self.driver.get(self.url)

    def _is_on_the_page(self):
        return self._clean_url(self.driver.current_url) == self.url

    @staticmethod
    def _clean_url(url):
        return urlunparse(urlparse(url)[:3] + ('', '', ''))
