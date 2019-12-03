# -*- coding: utf-8 -*-
"""
This file contains a generic HTML document class to make the analysis easier
and clearer. It is used by all the analysis on HTML documents.
"""

import bs4
from bs4 import BeautifulSoup

import re

import html_page
import util

class html_document(object):
    """
    This class encapsulates an html document. It provides useful methods for
    parsing html.
    
    ...
    
    Attributes
    ----------
    html_file: file
        the original .html file from which the document was created
    document_soup: bs4.BeautifulSoup
        the soup for the document, used for html parsing
    left_location_styles: dict
        a dictionary describing left position styles in document's css.
        elements are formatted as <css selector>: <pixels>
    bottom_location_styles: dict
        same as left_location_styles for bottom position
    width_styles: dict
        a dictionary describing width styles in document's css.
        elements are formatted as <css selector>: <pixels>
    height_styles: dict
        same as width_styles for height
    pages: list
        a list of html_page.html_page instances representing the document's
        pages. list is ordered from first to last page
    
    Methods
    ----------
    get_html_bbox_single(html_element)
        gets the bounding box of an html element according to the
        document's css, but does not search the element's children
    get_html_bbox(html_element)
        gets the bounding box of an html element according to the
        document's css, but also searches the element's first layer
        of children in case a child element's size exceeds the root
    get_font_info(html_element)
        gets font-family, font-size, font-color classes used in a html
        element, according to this document's css
    get_font_size(html_element)
        gets the font-size used by the html element, according to this
        document's css
    get_toc_pdf()
        gets a string representation of the document's table of
        contents, according to the pdf -> html conversion
    """
    
    # regex patterns to parse css styles in document to something usable
    # first capturing group is css selector, second capturing group is
    # the number of pixels
    X_REGEX = r'(\.x(?:[a-f0-9]{1,10})){left:(-?\d+(?:\.\d+)?)p[tx];}'
    Y_REGEX = r'(\.y(?:[a-f0-9]{1,10})){bottom:(-?\d+(?:\.\d+)?)p[tx];}'
    W_REGEX = r'(\.w(?:[a-f0-9]{1,10})){width:(-?\d+(?:\.\d+)?)p[tx];}'
    H_REGEX = r'(\.h(?:[a-f0-9]{1,10})){height:(-?\d+(?:\.\d+)?)p[tx];}'
    FS_REGEX= r'(\.fs(?:[a-f0-9]{1,10})){font-size:(-?\d+(?:\.\d+)?)p[tx];}'
    
    
    def __init__(self, html_file, extract_images=True):
        """
        Parameters
        ----------
        html_file: file
            the file to create an html document from, should be
            a valid .html file
        extract_images: boolean (optional, default=True)
            a keyword argument specifying if the document's images
            are required. If the analysis does not require images,
            then setting this argument to False will greatly speed up
            the runtime
        """
        self.html_file = html_file
        self.document_soup = BeautifulSoup(html_file, features="lxml")
        
        # css styles (for locations, sizes, font-types, etc)
        self.left_location_styles = {} # class styles with name x-something
        self.bottom_location_styles = {} # class styles with name y-something
        self.width_styles = {} # class styles with name w-something
        self.height_styles = {} # class styles with name h-something
        self.font_size_styles = {} # class styles with name fs-something
        
        # parse the document's css styles
        self._parse_css()
        
        # image hashes so duplicate images get ignored
        self.image_hashes = set([])
        
        # get all pages
        pages_soup = self.document_soup.find_all("div", {"data-page-no" : True})
        self.pages = list(map(lambda page_soup: html_page.html_page(self, page_soup, extract_images), pages_soup))
    
    
    def _parse_css(self):
        """
        Parses the document's inline css to get relevant styles
        """
        for style in self.document_soup.find_all("style"):
            # remove the large base64 encoded data from the text to speed
            # up regular expression search
            style_text = re.sub(r'base64,([^=]*)=\"', 'a', style.text)
            
            # find all css styles related to the class of interest, and
            # map the class to the number of pixels
            
            x_styles = re.findall(self.X_REGEX, style_text)
            for rule in x_styles:
                self.left_location_styles[rule[0]] = rule[1]
            
            y_styles = re.findall(self.Y_REGEX, style_text)
            for rule in y_styles:
                self.bottom_location_styles[rule[0]] = rule[1]
            
            w_styles = re.findall(self.W_REGEX, style_text)
            for rule in w_styles:
                self.width_styles[rule[0]] = rule[1]
                
            h_styles = re.findall(self.H_REGEX, style_text)
            for rule in h_styles:
                self.height_styles[rule[0]] = rule[1]
                
            fs_styles = re.findall(self.FS_REGEX, style_text)
            for rule in fs_styles:
                self.font_size_styles[rule[0]] = rule[1]
            
                
    def get_html_bbox_single(self, html_element):
        """
        Gets the bounding box of a html element according to this document's
        css. This method only searches the root element.
        
        Parameters
        ----------
        html_element: bs4.element.Tag
            the html element to get a bounding box for
            
        Returns
        ----------
        tuple
            a tuple of the form (x, y, w, h) containing floats representing
            the element's bounding box. x-y origin is at the bottom-left
            corner of the page, and y increases up the page.
        """
        if type(html_element) == bs4.element.Tag:
            # get all classes used by this element
            classes = html_element.attrs['class']
    
            def _find_style_pixels(class_prefix, class_styles):
                """
                Use the class to get the corresponding style
                """
                classes_with_prefix = [x for x in classes if re.match(class_prefix + '[a-f0-9]{1,10}', x)]
                if len(classes_with_prefix) > 0:
                    style_string = class_styles['.' + classes_with_prefix[0]]
                    return float(style_string)
                else:
                    return None
    
            x = _find_style_pixels("x", self.left_location_styles)
            y = _find_style_pixels("y", self.bottom_location_styles)
            w = _find_style_pixels("w", self.width_styles)
            h = _find_style_pixels("h", self.height_styles)
            
            return x, y, w, h
        else:
            return None, None, None, None

    def get_html_bbox(self, html_element):
        """
        Gets a bounding box of a html element according to this document's
        css. This method searches the first layer of children as well, in case
        a child element has a greater height/width than the root.
        
        Parameters
        ----------
        html_element: bs4.element.Tag
            the html element to get a bounding box for
            
        Returns
        ----------
        tuple
            a tuple of the form (x, y, w, h) containing floats representing
            the element's bounding box. x-y origin is at the bottom-left
            corner of the page, and y increases up the page.
        """
        x, y, w, h = self.get_html_bbox_single(html_element)
        if type(html_element) == bs4.element.Tag:
            for content in html_element.contents:
                x_, y_, w_, h_ = self.get_html_bbox_single(content)
                x = util.get_min_or_none(x, x_)
                y = util.get_min_or_none(y, y_)
                w = util.get_max_or_none(w, w_)
                h = util.get_max_or_none(h, h_)
        
        return x, y, w, h
    
    
    def get_font_info(self, html_element):
        """
        Gets all the font classes used by a html element.
        
        Parameters
        ----------
        html_element: bs4.element.Tag
            the html element to get font information for
        
        Returns
        ----------
        tuple
            a tuple of the form (ff, fs, fc) containing strings representing
            the font-family, font-size, and font-color classes used by
            the html element. Note that this does not return the actual content
            of the classes, but just the class names.
            html elements with only whitespace are ignored.
        """
        # get all text contained in this element
        text = util.get_descendent_text(html_element)
        if type(html_element) == bs4.element.Tag and text != '' and not text.isspace():
            # get all classes used by this element
            classes = html_element.attrs['class']
            
            def _find_style(class_prefix):
                """
                Use the class to find the corresponding style
                """
                classes_with_prefix = [x for x in classes if x.startswith(class_prefix)]
                if len(classes_with_prefix) > 0:
                    return classes_with_prefix[0]
                else:
                    return None
            
            # construct sets containing all the font-family, font-size, and font-color used in this element
            ff, fs, fc = set([_find_style('ff')]), set([_find_style('fs')]), set([_find_style('fc')])
            
            # recursive call
            for content in html_element.contents:
                ff_, fs_, fc_ = self.get_font_info(content)
                ff, fs, fc = ff.union(ff_), fs.union(fs_), fc.union(fc_)
        else:
            ff, fs, fc = set(), set(), set()
        
        return ff, fs, fc
    
    
    def get_font_size(self, html_element):
        """
        Gets the font size used by the html element. Does not consider
        the element's descendents.
        
        Parameters
        ----------
        html_element: bs4.element.Tag
            the html element to get the font size used
        
        Returns
        ----------
        float or None
            the font size used by the html element, in pixels, or None
            if not found
        """
        if type(html_element) == bs4.element.Tag:
            # get all classes this element uses
            classes = html_element.attrs['class']
            # use class to get the corresponding style
            for css_class in classes:
                if css_class.startswith('fs'):
                    style_string = self.font_size_styles['.' + css_class]
                    return float(style_string)
        
        return None


    def get_toc_pdf(self):
        """
        Gets the table of contents of this document, according to the
        pdf -> html conversion library (pdf2html).
        This means if no table of contents was explicitly created in the pdf,
        this method would not find a table of contents.
        A probably better method can be found in the functions used by
        html_analyzer, specifically html_analyzer.get_toc_pages and 
        html_analyzer.construct_toc. These functions do not rely on the
        pdf -> html library to provide the table of contents.
        
        Returns
        ----------
        str or None
            a string representation of the table of contents in the document,
            or None if no table was found.
        """
        # find the outer container for the table of contents
        table_of_contents_html = self.document_soup.find("div", {"id" : "outline"})
        if not table_of_contents_html: return None
        
        def _traverse_table_of_contents(root, level):
            """
            Traverses the table of contents tree, adding rows to it as text
            during the traversal
            """
            if type(root) == bs4.element.Tag:
                if root.name == 'ul' or root.name == 'li' or root.name == 'div':
                    # root is top-level of list, will have child elements
                    if root.name == 'ul':
                        level += 1
                    
                    text_ = ""
                    for content in root.contents:
                        level_text = _traverse_table_of_contents(content, level)
                        if level_text is not None and not level_text.isspace():
                            if not level_text.endswith("\n"):
                                text_ += level_text + "\n"
                            else:
                                text_ += level_text
                    return text_
                        
                elif root.name == 'a':
                    return '-' * level + root.text
        
        return _traverse_table_of_contents(table_of_contents_html, 0)
  
                