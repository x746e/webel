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


# TODO: Rename selectors to locators
def parse_selector(selector):
    if '=' not in selector:
        return By.ID, selector
    strategy_str, value = selector.split('=', 1)
    strategy = str_to_strategy[strategy_str]
    return strategy, value


def get_element_by_selector(selector, container=None):
    elements = get_elements_by_selector(selector, container=container)
    if len(elements) == 0:
        raise NoSuchElementException('%r is not found' % selector)
    if len(elements) > 1:
        raise MultipleElementsSelectedException(
            '%r returned more than one element (%d)' % (
                selector, len(elements)))
    return elements[0]


def get_elements_by_selector(selector, container=None):
    if container is None:
        container = get_driver()
    strategy, value = parse_selector(selector)
    return container.find_elements(by=strategy, value=value)


class Element(object):

    def __init__(self, selector):
        self.selector = selector

    # TODO: rename to get_webelement (and all other webelements).
    def get_element(self, page, timeout=10):
        # TODO: remove `get_driver()`
        container = getattr(page, 'element', None)
        driver = get_driver() if container is None else container
        # XXX: Will it fail when there are several elements returned by `self.selector`?
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(parse_selector(self.selector)),
            message="Can't get %r element" % self.selector
        )
        return element


# TODO: Create one abstract Text element and to implementations: TextInput and TextArea.
class Text(Element):

    def __get__(self, page, type):
        return self.get_element(page).get_attribute('value')

    def __set__(self, page, value):
        el = self.get_element(page)
        el.click()
        el.send_keys(value)


class ReadOnlyText(Element):

    def __get__(self, page, type):
        element = self.get_element(page)
        return element.text


class Checkbox(Element):

    def __get__(self, page, type):
        element = self.get_element(page)
        return element.is_selected()

    def __set__(self, page, value):
        element = self.get_element(page)
        if element.is_selected() != value:
            element.click()


class LinkObject(object):

    def __init__(self, container, element, to_page_cls):
        self.container = container
        self.element = element
        self.to_page_cls = to_page_cls

    def __call__(self):
        self.click()

    def click(self):
        self.element.click()
        if self.to_page_cls is not None:
            page = self.to_page_cls(assert_is_on_page=True)
            return page


class Link(Element):

    def __init__(self, selector, to=None):
        super(Link, self).__init__(selector)
        self.to_page_cls = to

    def __get__(self, container, type):
        return LinkObject(container, self.get_element(container), self.to_page_cls)


Button = Link


class FragmentObject(object):

    def __init__(self, element, container=None):
        self.container = container
        self.element = element


class Fragment(Element):

    def __init__(self, selector, fragment_cls):
        super(Fragment, self).__init__(selector)
        self.fragment_cls = fragment_cls

    def __get__(self, container, type):
        return self.fragment_cls(self.get_element(container), container)


class Page(object):

    url = None

    # XXX: make assert_is_on_page hidden?
    def __init__(self, load=None, assert_is_on_page=None):
        if load is None and assert_is_on_page is None:
            assert self.url is not None, "Don't now what to do."
            if not self.is_on_the_page():
                self.load()

        if load is True and assert_is_on_page is True:
            raise TypeError("That's not valid to set `load` and "
                            "`assert_is_assert_is_on_page` to True at the same time.")

        if assert_is_on_page and self.url is not None:
            assert self.is_on_the_page()

        if load:
            self.load()

        self.element = get_driver()

    def load(self):
        get_driver().get(self.url)

    def is_on_the_page(self):
        return self._clean_url(get_driver().current_url) == self.url

    @staticmethod
    def _clean_url(url):
        return urlunparse(urlparse(url)[:3] + ('', '', ''))
