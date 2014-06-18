from urlparse import urlparse, urlunparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webel.exceptions import NoSuchElementException, MultipleElementsSelectedException


driver = None


def set_driver(b):
    global driver
    driver = b


def get_driver():
    return driver


str_to_strategy = {
    'id': By.ID,
    'xpath': By.XPATH,
    'name': By.NAME,
    'class': By.CLASS_NAME,
    'css': By.CSS_SELECTOR,
    'link_text': By.LINK_TEXT,
    'tag_name': By.TAG_NAME,
}


def parse_locator(locator):
    if '=' not in locator:
        return By.ID, locator
    strategy_str, value = locator.split('=', 1)
    strategy = str_to_strategy[strategy_str]
    return strategy, value


def get_element_by_locator(locator, container=None):
    elements = get_elements_by_locator(locator, container=container)
    if len(elements) == 0:
        raise NoSuchElementException('%r is not found' % locator)
    if len(elements) > 1:
        raise MultipleElementsSelectedException(
            '%r returned more than one element (%d)' % (
                locator, len(elements)))
    return elements[0]


def get_elements_by_locator(locator, container=None):
    if container is None:
        container = get_driver()
    strategy, value = parse_locator(locator)
    return container.find_elements(by=strategy, value=value)


class Element(object):

    def __init__(self, locator):
        self.locator = locator

    def get_webelement(self, page, timeout=10):
        # TODO: remove `get_driver()`
        container = getattr(page, 'webelement', None)
        driver = get_driver() if container is None else container
        # XXX: Will it fail when there are several elements returned by `self.locator`?
        webelement = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(parse_locator(self.locator)),
            message="Can't get %r element" % self.locator
        )
        return webelement


# TODO: Create one abstract Text element and to implementations: TextInput and TextArea.
class Text(Element):

    def __get__(self, page, type):
        return self.get_webelement(page).get_attribute('value')

    def __set__(self, page, value):
        el = self.get_webelement(page)
        el.click()
        el.send_keys(value)


class ReadOnlyText(Element):

    def __get__(self, page, type):
        webelement = self.get_webelement(page)
        return webelement.text


class Checkbox(Element):

    def __get__(self, page, type):
        webelement = self.get_webelement(page)
        return webelement.is_selected()

    def __set__(self, page, value):
        webelement = self.get_webelement(page)
        if webelement.is_selected() != value:
            webelement.click()


class LinkObject(object):

    def __init__(self, container, webelement, to_page_cls):
        self.container = container
        self.webelement = webelement
        self.to_page_cls = to_page_cls

    def __call__(self):
        return self.click()

    def click(self):
        self.webelement.click()
        if self.to_page_cls is not None:
            assert_is_on_page = self.to_page_cls.url is not None
            page = self.to_page_cls(assert_is_on_page=assert_is_on_page)
            return page


class Link(Element):

    def __init__(self, locator, to=None):
        super(Link, self).__init__(locator)
        self.to_page_cls = to

    def __get__(self, container, type):
        return LinkObject(container, self.get_webelement(container), self.to_page_cls)


Button = Link


class FragmentObject(object):

    def __init__(self, webelement, container=None):
        self.container = container
        self.webelement = webelement


class Fragment(Element):

    def __init__(self, locator, fragment_cls):
        super(Fragment, self).__init__(locator)
        self.fragment_cls = fragment_cls

    def __get__(self, container, type):
        return self.fragment_cls(self.get_webelement(container), container)


class Page(object):

    url = None

    def __init__(self, load=None, assert_is_on_page=None):
        if load is True and assert_is_on_page is True:
            raise TypeError("That's not valid to set `load` and "
                            "`assert_is_assert_is_on_page` to True at the same time.")

        if (assert_is_on_page or load) and self.url is None:
            raise TypeError("Page need `self.url` for assert_is_on_page or load.")

        if assert_is_on_page:
            assert self._is_on_the_page()

        if load:
            self.load()

        self.webelement = get_driver()

    def load(self):
        get_driver().get(self.url)

    def _is_on_the_page(self):
        return self._clean_url(get_driver().current_url) == self.url

    @staticmethod
    def _clean_url(url):
        return urlunparse(urlparse(url)[:3] + ('', '', ''))
