from selenium.webdriver.support.wait import WebDriverWait

from webel.exceptions import MultipleElementsSelectedException
from webel.webelement_getters import get_element, get_elements


class Element(object):

    def __init__(self, locator):
        self.locator = locator

    def get_webelement(self, container, timeout=20):
        # TODO: move waiting to `webelement_getters`.
        webelement = WebDriverWait(
            container.webelement,
            timeout, ignored_exceptions=(MultipleElementsSelectedException,)
        ).until(
            lambda driver: get_element(self.locator, driver),
			# XXX: there can be several options: not only not found, by it will fail
			# with the same message when there are several elements returned by the
			# locator.  Probably it's worth reimplementing WebDriverWait.
            message="Can't get %r element" % self.locator
        )
        return webelement


# TODO: Create one abstract Text element and to implementations: TextInput and TextArea.
class Text(Element):

    def __get__(self, container, container_cls):
        return self.get_webelement(container).get_attribute('value')

    def __set__(self, container, value):
        el = self.get_webelement(container)
        el.click()
        el.send_keys(value)


class CheckingText(Element):

    """
    Like `Text`, but checks if the text appeared in the element, and fails if not.

    May be helpful when dealing with tricky javascript-heavy controls.
    """

    def __get__(self, container, container_cls=None):
        return self.get_webelement(container).get_attribute('value')

    def __set__(self, container, value):
        el = self.get_webelement(container)
        el.click()
        el.send_keys(value)
        self.check(container, value)

    def check(self, container, value):
        new_value = self.__get__(container)
        assert value == new_value



class ReadOnlyText(Element):

    def __get__(self, container, container_cls):
        webelement = self.get_webelement(container)
        return webelement.text


class Checkbox(Element):

    def __get__(self, container, container_cls):
        webelement = self.get_webelement(container)
        return webelement.is_selected()

    def __set__(self, container, value):
        webelement = self.get_webelement(container)
        if webelement.is_selected() != value:
            webelement.click()


class LinkObject(object):

    def __init__(self, webelement, to_page_cls):
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

    def __get__(self, container, container_cls):
        return LinkObject(self.get_webelement(container), self.to_page_cls)


Button = Link


class ElementList(object):

    def __init__(self, locator, list_object_cls):
        self.locator = locator
        self.list_object_cls = list_object_cls

    def __get__(self, container, container_cls):
        # TODO: move waiting to `webelement_getters`.
        timeout = 10
        webelements = WebDriverWait(
            container.webelement, timeout,
        ).until(
            lambda driver: get_elements(self.locator, driver),
            message="Can't get %r elements" % self.locator
        )
        return [
            self.list_object_cls(webelement) for webelement in webelements
        ]


class FragmentObject(object):

    def __init__(self, webelement):
        self.webelement = webelement


class Fragment(Element):

    def __init__(self, locator, fragment_object_cls):
        super(Fragment, self).__init__(locator)
        self.fragment_object_cls = fragment_object_cls

    def __get__(self, container, container_cls):
        return self.fragment_object_cls(self.get_webelement(container))
