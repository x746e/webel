from mock import Mock
from unittest import TestCase, skip
from selenium.webdriver.common.by import By

from webel.exceptions import (
    NoSuchElementException, MultipleElementsSelectedException, TimeoutException,)
from webel.driver import set_driver
from webel.webelement_getters import parse_locator, get_element, get_elements
from webel.elements import (
    Element, Text, ReadOnlyText, Checkbox, Link, FragmentObject, Fragment,
    ElementList)
from webel.page import Page


class ParseLocatorTests(TestCase):

    def test_parse_locator(self):
        self.assertEqual(parse_locator("xpath=//div[text()='']"),
                         (By.XPATH, "//div[text()='']"))

    def test_parse_locator_default(self):
        self.assertEqual(parse_locator("id_whatever"), (By.CSS_SELECTOR, "id_whatever"))


class GettingElementsTests(TestCase):

    def test_get_elements(self):
        mocked_driver = Mock()
        set_driver(mocked_driver)
        get_elements('id=whatever')
        mocked_driver.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_elements_with_a_container(self):
        container = Mock()
        get_elements('id=whatever', container=container)
        container.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element(self):
        mocked_driver = Mock(**{'find_elements.return_value': [Mock()]})
        set_driver(mocked_driver)
        get_element('id=whatever')
        mocked_driver.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_with_a_container(self):
        container = Mock(**{'find_elements.return_value': [Mock()]})
        get_element('id=whatever', container=container)
        container.find_elements.assert_called_once_with(by=By.ID, value='whatever')

    def test_get_element_should_raise_when_no_elements_found(self):
        container = Mock(**{'find_elements.return_value': []})
        with self.assertRaises(NoSuchElementException):
            get_element('whatever', container=container)

    def test_get_element_should_raise_when_several_elements_found(self):
        container = Mock(**{'find_elements.return_value': [Mock(), Mock()]})
        with self.assertRaises(MultipleElementsSelectedException):
            get_element('whatever', container=container)


class ElementTests(TestCase):

    def test_get_element(self):
        webdriver_element = Mock()
        page = Mock(**{'webelement.find_elements.return_value': [webdriver_element]})
        element = Element('xpath=//div')
        self.assertEqual(element.get_webelement(page), webdriver_element)
        page.webelement.find_elements.assert_called_once_with(
            by='xpath', value='//div')

    def test_raises_when_no_elements(self):
        page = Mock(**{'webelement.find_elements.return_value': []})
        element = Element('xpath=//div')
        with self.assertRaises(TimeoutException):
            element.get_webelement(page, timeout=.1)

    def test_raises_when_several_elements(self):
        page = Mock(**{'webelement.find_elements.return_value': [Mock(), Mock()]})
        element = Element('xpath=//div')
        with self.assertRaises(TimeoutException):
            element.get_webelement(page, timeout=.1)


class ElementSubclassesTests(TestCase):

    def setUp(self):
        class TestPage(Page):
            text = Text('whatever')
            ro_text = ReadOnlyText('ro_text_locator')
            cbox = Checkbox('cbox_locator')
        self.webelement = Mock()
        self.driver = Mock(**{'find_elements.return_value': [self.webelement]})
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
        self.driver = Mock(**{'find_elements.return_value': [self.webelement]})
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


class ElementListTests(TestCase):

    def test_it(self):
        lis_webobjects = [Mock(), Mock(), Mock()]
        mocked_driver = Mock(**{'find_elements.return_value': lis_webobjects})
        set_driver(mocked_driver)
        class TestPage(Page):
            lis = ElementList('ul > lis', FragmentObject)
        page = TestPage()

        lis = page.lis
        self.assertEqual(len(lis), 3)
        self.assertIs(lis[1].webelement, lis_webobjects[1])


class FragmentTests(TestCase):

    def setUp(self):
        self.element = Mock()
        self.container = Mock(**{'find_elements.return_value': [self.element]})
        self.mocked_driver = Mock(**{'find_elements.return_value': [self.container]})
        set_driver(self.mocked_driver)

        class TestFragmentObject(FragmentObject):
            input = Text('css=.whatever')

        class TestPage(Page):
            fragment = Fragment('id=fragment_id', TestFragmentObject)

        self.page = TestPage()

    def test_getting_fragment(self):
        fragment = self.page.fragment
        self.mocked_driver.find_elements.assert_called_once_with(
            by=By.ID, value='fragment_id')

    def test_elements_on_fragment(self):
        fragment = self.page.fragment
        fragment.input = 'lalala'
        self.element.send_keys.assert_called_once_with('lalala')


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
        page = self.TestPage(assert_is_on_page=False)
        self.assertFalse(self.mocked_driver.get.called)
        page = self.TestPage(load=False, assert_is_on_page=False)
        self.assertFalse(self.mocked_driver.get.called)

    def test_page_without_url(self):
        class PageWithoutURL(Page):
            pass
        PageWithoutURL()

    def test_assert_is_on_page(self):
        self.mocked_driver.current_url = 'http://example.org/?lala=1'
        self.TestPage(assert_is_on_page=True, timeout=.1)
        self.mocked_driver.current_url = 'http://example.org/whatever/'
        with self.assertRaises(TimeoutException):
            self.TestPage(assert_is_on_page=True, timeout=.1)

    def test_assert_is_on_page_with_fragment(self):
        class URLFragmentPage(Page):
            url = 'http://example.org/courses/#/course/CRS1'
        self.mocked_driver.current_url = 'http://example.org/courses/#/course/CRS1'
        URLFragmentPage(assert_is_on_page=True, timeout=.1)
        self.mocked_driver.current_url = 'http://example.org/courses/#/course/WTWR1'
        with self.assertRaises(TimeoutException):
            URLFragmentPage(assert_is_on_page=True, timeout=.1)

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


class PageParametersTests(TestCase):

    def setUp(self):
        self.mocked_driver = Mock()
        set_driver(self.mocked_driver)

    def test_parametrized_assert_is_on_page(self):
        class ParametrizedPage(Page):
            url = 'http://example.org/courses/#/course/{slug}'
        self.mocked_driver.current_url = 'http://example.org/courses/#/course/CRS1'
        ParametrizedPage(slug='CRS1', assert_is_on_page=True, timeout=.1)
        with self.assertRaises(TimeoutException):
            ParametrizedPage(slug='WTWR1', assert_is_on_page=True, timeout=.1)

    def test_wrong_parameters_to_the_page(self):
        class ExcessPage1(Page):
            pass
        with self.assertRaises(TypeError):
            ExcessPage1(aa=1)

        class Page2(Page):
            url = 'http://example.org/{whtvr}/'
        with self.assertRaises(TypeError):
            Page2(whtvr=1, rvthw=2)
        with self.assertRaises(TypeError):
            Page2(rvthw=2)

    def test_url_should_be_checked_when_it_is_parametrized_and_no_kwargs_are_provided(self):
        class TestPage(Page):
            url = 'http://example.org/{whatever}/'

        self.mocked_driver.current_url = 'http://example.org/aaaaa/'
        TestPage(assert_is_on_page=True, timeout=.1)

        self.mocked_driver.current_url = 'http://example.org/whatever/and/ever/'
        with self.assertRaises(TimeoutException):
            TestPage(assert_is_on_page=True, timeout=.1)

    def test_parameters_should_be_extracted_from_url(self):
        class TestPage(Page):
            url = 'http://example.org/{whatever}/'

        self.mocked_driver.current_url = 'http://example.org/aaaaa/'
        page = TestPage(assert_is_on_page=True, timeout=.1)

        self.assertEqual(page.params['whatever'], 'aaaaa')
