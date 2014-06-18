from mock import Mock
from unittest import TestCase
from selenium.webdriver.common.by import By

from webel.exceptions import NoSuchElementException, MultipleElementsSelectedException
from webel.elements import (
    parse_locator, get_elements_by_locator, get_element_by_locator, set_driver,
    Element, Text, Page, ReadOnlyText, Checkbox, Link, FragmentObject, Fragment)


class ParseLocatorTests(TestCase):

    def test_parse_locator(self):
        self.assertEqual(parse_locator("xpath=//div[text()='']"),
                         (By.XPATH, "//div[text()='']"))

    def test_parse_locator_default(self):
        # TODO: Change default to css
        self.assertEqual(parse_locator("id_whatever"), (By.ID, "id_whatever"))


class GettingElementsTests(TestCase):

    def test_get_elements_by_locator(self):
        mocked_driver = Mock()
        set_driver(mocked_driver)
        get_elements_by_locator('whatever')
        mocked_driver.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_elements_by_locator_with_a_container(self):
        container = Mock()
        get_elements_by_locator('whatever', container=container)
        container.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_by_locator(self):
        mocked_driver = Mock(**{'find_elements.return_value': [Mock()]})
        set_driver(mocked_driver)
        get_element_by_locator('whatever')
        mocked_driver.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_by_locator_with_a_container(self):
        container = Mock(**{'find_elements.return_value': [Mock()]})
        get_element_by_locator('whatever', container=container)
        container.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_by_locator_should_raise_when_no_elements_found(self):
        container = Mock(**{'find_elements.return_value': []})
        with self.assertRaises(NoSuchElementException):
            get_element_by_locator('whatever', container=container)

    def test_get_element_by_locator_should_raise_when_several_elements_found(self):
        container = Mock(**{'find_elements.return_value': [Mock(), Mock()]})
        with self.assertRaises(MultipleElementsSelectedException):
            get_element_by_locator('whatever', container=container)


class ElementTests(TestCase):

    def test_get_element(self):
        webdriver_element = Mock()
        page = Mock(**{'webelement.find_element.return_value': webdriver_element})
        element = Element('xpath=//div')
        self.assertEqual(element.get_webelement(page), webdriver_element)
        page.webelement.find_element.assert_called_once_with('xpath', '//div')

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
        text = self.page.text
        self.webelement.get_attribute.assert_called_once_with('value')

    def test_text_write(self):
        self.page.text = 'hello'
        self.webelement.send_keys.assert_called_once_with('hello')

    def test_read_only_text_read(self):
        self.webelement.text = 'ro_text'
        self.assertEqual(self.page.ro_text, 'ro_text')

    def test_checkbox_read(self):
        is_checked = self.page.cbox
        self.webelement.is_selected.assert_called_once_with()

    def test_checkbox_write(self):
        self.webelement.is_selected.return_value = True
        self.page.cbox = True
        self.assertFalse(self.webelement.click.called)
        self.page.cbox = False
        self.webelement.click.assert_called_once_with()


class LinkTests(TestCase):

    def setUp(self):
        self.other_page_cls = Mock()
        class TestPage(Page):
            clickme = Link('id=clickme')
            linktopage = Link('id=linktopage', to=self.other_page_cls)
        self.webelement = Mock()
        self.driver = Mock(**{'find_element.return_value': self.webelement})
        set_driver(self.driver)
        self.page = TestPage(assert_is_on_page=False)

    def test_call(self):
        ret = self.page.clickme()
        self.assertIsNone(ret)
        self.webelement.click.assert_called_once_with()

    def test_click(self):
        ret = self.page.clickme.click()
        self.assertIsNone(ret)
        self.webelement.click.assert_called_once_with()

    def test_to_page(self):
        page = self.page.linktopage()
        self.other_page_cls.assert_called_once_with(assert_is_on_page=True)
        self.assertIs(page, self.other_page_cls())

    def test_to_page_without_url(self):
        other_page_cls = Mock(url=None)
        class TestPage(Page):
            linktopage = Link('id=linktopage', to=other_page_cls)
        page = TestPage()
        page.linktopage()
        other_page_cls.assert_called_once_with(assert_is_on_page=False)


class FragmentTests(TestCase):

    def setUp(self):
        self.mocked_driver = Mock()
        set_driver(self.mocked_driver)

        class TestFragmentObject(FragmentObject):
            input = Text('css=.whatever')

        class TestPage(Page):
            fragment = Fragment('id=fragment_id', TestFragmentObject)

        self.page = TestPage()

    def test_getting_fragment(self):
        fragment = self.page.fragment
        self.mocked_driver.find_element.assert_called_once_with(By.ID, 'fragment_id')

    def test_elements_on_fragment(self):
        fragment = self.page.fragment
        fragment.input = 'lalala'
        fragment.webelement.find_element().send_keys.assert_called_once_with('lalala')


class PageTests(TestCase):

    def setUp(self):
        self.mocked_driver = Mock()
        set_driver(self.mocked_driver)
        class TestPage(Page):
            url = 'http://example.org/'
        self.TestPage = TestPage

    def test_load(self):
        page = self.TestPage(load=True)
        self.mocked_driver.get.assert_called_once_with('http://example.org/')

    def test_load_is_disabled_by_default(self):
        page = self.TestPage()
        self.assertFalse(self.mocked_driver.get.called)
        page = self.TestPage(load=False)
        self.assertFalse(self.mocked_driver.get.called)

    def test_assert_is_on_page(self):
        self.mocked_driver.current_url = 'http://example.org/?lala=1'
        page = self.TestPage(assert_is_on_page=True)
        self.mocked_driver.current_url = 'http://example.org/whatever/'
        with self.assertRaises(AssertionError):
            page = self.TestPage(assert_is_on_page=True)

    def test_is_on_page(self):
        page = self.TestPage()
        self.mocked_driver.current_url = 'http://example.org/?lala=1'
        self.assertTrue(page._is_on_the_page())
        self.mocked_driver.current_url = 'http://example.org/whatever/'
        self.assertFalse(page._is_on_the_page())

    def test_load_and_assert_is_on_page_at_the_same_time(self):
        with self.assertRaises(TypeError):
            self.TestPage(load=True, assert_is_on_page=True)

    def test_assert_is_on_page_without_url(self):
        class TestPage(Page):
            pass
        with self.assertRaises(TypeError):
            page = TestPage(assert_is_on_page=True)

    def test_clean_url(self):
        self.assertEqual(Page._clean_url('http://example.org/?lalal&ss&dd=1'),
                         'http://example.org/')
        self.assertEqual(Page._clean_url('http://example.org/some/path/?lalal=2'),
                         'http://example.org/some/path/')
        self.assertEqual(Page._clean_url('http://example.org/w/o/slash?lalal=a'),
                         'http://example.org/w/o/slash')
        self.assertEqual(Page._clean_url('http://example.org/w/o/slash?lalal=b'),
                         'http://example.org/w/o/slash')
        self.assertEqual(Page._clean_url('/some/path?lala=1'), '/some/path')
