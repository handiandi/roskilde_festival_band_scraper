from bs4 import BeautifulSoup
import itertools


class Parser(object):

    """docstring for Parser"""

    def __init__(self):
        pass

    def test(self, html_doc):
        soup = BeautifulSoup(html_doc)  # 'html.parser')

    def get_element(self, node):
        # for XPATH we have to count only for nodes with same type!
        length = len(list(node.previous_siblings)) + 1
        if (length) > 1:
            return '%s:nth-child(%s)' % (node.name, length)
        else:
            return node.name

    def get_css_path_helper(self, node):
        path = [self.get_element(node)]
        for parent in node.parents:
            if parent.name == 'body':
                break
            path.insert(0, self.get_element(parent))
        return ' > '.join(path)

    def get_xpath(self, element):
        """
        Generate xpath of soup element
        :param element: bs4 text or node
        :return: xpath as string
        """
        components = []
        child = element if element.name else element.parent
        for parent in child.parents:
            """
            @type parent: bs4.element.Tag
            """
            previous = itertools.islice(parent.children, 0, parent.contents.index(child))
            xpath_tag = child.name
            xpath_index = sum(1 for i in previous if i.name == xpath_tag) + 1
            components.append(xpath_tag if xpath_index == 1 else '%s[%d]' % (xpath_tag, xpath_index))
            child = parent
        components.reverse()
        return '/%s' % '/'.join(components)