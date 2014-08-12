from selenium.webdriver.common.by import By

from webel.driver import get_driver
from webel.exceptions import NoSuchElementException, MultipleElementsSelectedException


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
        return By.CSS_SELECTOR, locator
    strategy, value = locator.split('=', 1)
    if strategy not in str_to_strategy:
        return By.CSS_SELECTOR, locator
    return str_to_strategy[strategy], value


# TODO: s/\<element/webelement
def get_element(locator, container=None, only_visible=True):
    all_elements = get_elements(locator, container=container)
    if only_visible:
        elements = [element for element in all_elements if element.is_displayed()]
    else:
        elements = all_elements

    if only_visible and not elements:
        raise NoSuchElementException('%r does not become visible')
    elif not elements:
        raise NoSuchElementException('%r is not found' % locator)
    if len(elements) > 1:
        raise MultipleElementsSelectedException(
            '%r returned more than one element (%d)' % (
                locator, len(elements)))
    return elements[0]


def get_elements(locator, container=None):
    if container is None:
        container = get_driver()
    strategy, value = parse_locator(locator)
    return container.find_elements(by=strategy, value=value)
