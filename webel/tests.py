from mock import Mock
from unittest import TestCase
from selenium.webdriver.common.by import By

from webel.exceptions import NoSuchElementException, MultipleElementsSelectedException
from webel.elements import (
    parse_selector, get_elements_by_selector, get_element_by_selector, set_driver,
    Element, Text, Page, ReadOnlyText, Checkbox)


# TODO: Rename selectors to locators
class ParseLocatorTests(TestCase):

    def test_parse_selector(self):
        self.assertEqual(parse_selector("xpath=//div[text()='']"),
                         (By.XPATH, "//div[text()='']"))

    def test_parse_selector_default(self):
        # TODO: Change default to css
        self.assertEqual(parse_selector("id_whatever"), (By.ID, "id_whatever"))


class GettingElementsTests(TestCase):

    def test_get_elements_by_locator(self):
        mocked_driver = Mock()
        set_driver(mocked_driver)
        get_elements_by_selector('whatever')
        mocked_driver.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_elements_by_locator_with_a_container(self):
        container = Mock()
        get_elements_by_selector('whatever', container=container)
        container.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_by_locator(self):
        mocked_driver = Mock(**{'find_elements.return_value': [Mock()]})
        set_driver(mocked_driver)
        get_element_by_selector('whatever')
        mocked_driver.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_by_locator_with_a_container(self):
        container = Mock(**{'find_elements.return_value': [Mock()]})
        get_element_by_selector('whatever', container=container)
        container.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_by_locator_should_raise_when_no_elements_found(self):
        container = Mock(**{'find_elements.return_value': []})
        with self.assertRaises(NoSuchElementException):
            get_element_by_selector('whatever', container=container)

    def test_get_element_by_locator_should_raise_when_several_elements_found(self):
        container = Mock(**{'find_elements.return_value': [Mock(), Mock()]})
        with self.assertRaises(MultipleElementsSelectedException):
            get_element_by_selector('whatever', container=container)


class ElementTests(TestCase):

    def test_get_element(self):
        webdriver_element = Mock()
        page = Mock(**{'element.find_element.return_value': webdriver_element})
        element = Element('xpath=//div')
        self.assertEqual(element.get_element(page), webdriver_element)
        page.element.find_element.assert_called_once_with('xpath', '//div')

    def test_raises_when_no_elements(self):
        pass  # TODO

    def test_raises_when_several_elements(self):
        pass  # TODO


class ElementSubclassesTests(TestCase):

    def setUp(self):
        class TestPage(Page):
            text = Text('whatever')
            ro_text = ReadOnlyText('ro_text_locator')
            cbox = Checkbox('cbox_locator')
        self.webelement = Mock()
        self.driver = Mock(**{'find_element.return_value': self.webelement})
        set_driver(self.driver)
        self.page = TestPage(assert_is_on_page=False)

    def test_text_read(self):
        self.page.text
        self.webelement.get_attribute.assert_called_once_with('value')

    def test_text_write(self):
        self.page.text = 'hello'
        self.webelement.send_keys.assert_called_once_with('hello')

    def test_read_only_text_read(self):
        self.webelement.text = 'ro_text'
        self.assertEqual(self.page.ro_text, 'ro_text')

    def test_checkbox_read(self):
        self.page.cbox
        self.webelement.is_selected.assert_called_once_with()

    def test_checkbox_write(self):
        self.webelement.is_selected.return_value = True
        self.page.cbox = True
        self.assertFalse(self.webelement.click.called)
        self.page.cbox = False
        self.webelement.click.assert_called_once_with()
