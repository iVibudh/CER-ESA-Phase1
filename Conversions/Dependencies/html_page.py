# -*- coding: utf-8 -*-
"""
This file contains a generic HTML page class to make the analysis easier
and clearer. It is used by all the analysis on HTML documents.
"""

import bs4
import base64 # for image extraction
#python -m pip install --upgrade pip
#python -m pip install opencv-python --user
import cv2
import hashlib
import numpy as np
import io

import util

import collections

"""
A container for data about an image in the html page.
Fields:
    "image":        a cv2 image (most of the time a numpy array)
                    representing the actual image data
    "bbox":         a tuple of the form (x, y, w, h) containing floats
                    representing the bounding box of the image in pixels, 
                    relative to the page. x-y origin is at the 
                    bottom-left corner of the page, and y increases 
                    up the page.
    "is_table":     a boolean indicating if the image was detected
                    as a table or not.
    "center":       a (x, y) tuple of floats representing the
                    center position of the image on the page. x-y
                    coordinate system is same as "bbox" field
    "fragmented":   a boolean indicating if other images were
                    extracted from the same parent image
"""
html_image = collections.namedtuple('html_image', 'image, bbox, is_table, center, fragmented')


"""
A container for data about text lines in the html page.
Fields:
    "text":             the actual text (string) content of the line
    "html":             the bs4.element.Tag representing the html element
                        containing the line
    "center":           a (x, y) tuple of floats representing the center
                        position of the image on the page. x-y origin is at
                        the bottom-left corner of the page, and y increases
                        up the page.
    "bbox":             a tuple of the form (x, y, w, h) containing floats
                        representing the bounding box of the line in
                        pixels. x-y coordinate system is same as "center" field
    "max_font_size":    a float indicating the maximum font size used in the line
"""
html_line = collections.namedtuple('html_line', 'text, html, center, bbox, max_font_size')


class html_page(object):
    """
    This class encapsulates a page in a html document.
    
    ...
    
    Attributes
    ----------
    html_document: html_document.html_document
        the outer html document from which the page was extracted
    page_soup: bs4.BeautifulSoup
        the soup for the page, used for html parsing
    page_width: float
        the width of the page in pixels
    page_height: float
        the height of the page in pixels
    images: list
        a list of all images identified in the page. Images are
        stored as html_page.html_image tuples. The list is sorted in the
        order images appear on the page, in vertical order (so the first image
        in the list is the top-most image)
    lines: list
        a list of all text lines identified in the page. Lines are
        stored as html_page.html_line tuples
    raw_lines: list
        a list of strings representing the raw text in the page. "Raw" means
        the function util.clean_text has not been applied on the string.
    text_lines: list
        a list of strings representing the text on the page. The function
        util.clean_text has been applied on the string.
    """
    
    
    def __init__(self, html_document, page_soup, extract_images=True):
        """
        Parameters
        ----------
        html_document: html_document.html_document
            the outer html document from which the page was extracted
        page_soup: bs4.BeautifulSoup:
            the soup for the page, used for html parsing
        extract_images: boolean (optional, default=True)
            a keyword argument specifying if the page's images
            are required. If the analysis does not require images,
            then setting this argument to False will greatly speed up
            the runtime
        """
        self.html_document = html_document
        self.page_soup = page_soup
        
        # get the size of the page
        _, _, self.page_width, self.page_height = html_document.get_html_bbox_single(page_soup)
        self.page_width, self.page_height = float(self.page_width), float(self.page_height)
        
        # extract images, lines, and text
        if extract_images:
            self.images = self._get_images()
        self.lines, self.raw_lines = self._get_lines()
        self.text_lines = self._get_text_lines()
    
    
    def _get_images(self):
        """
        Gets a list of all (processed) images identified in the page
        For more detail see documentation for "images" attribute
        """
        
        # find all images and record center coordinates
        images = []
        for i, image_html in enumerate(self.page_soup.find_all("img")):
            # get location information about whole image
            img_orig_x, img_orig_y, img_orig_w, img_orig_h = self.html_document.get_html_bbox_single(image_html)
            
            # get the image source and decode the Base64 string into a cv2 image
            img_src = image_html["src"]
            img_b64 = img_src.split("base64,")[1]
            img_raw = base64.b64decode(img_b64)
            img_stream = io.BytesIO(img_raw)
            img_orig = cv2.imdecode(np.fromstring(img_stream.read(), np.uint8), 1)
            
            # get the actual size of the image (the html documents often store
            # images with compressed sizes)
            img_orig_h_real, img_orig_w_real, _ = img_orig.shape
            
            # get compression ratio
            height_compression = float(img_orig_h) / img_orig_h_real
            width_compression = float(img_orig_w) / img_orig_w_real
            
            # list of all distinct images extracted from the original image
            trimmed_images = []
            
            for img_data in util.get_trimmed_images(img_orig):
                # detect if image is a table frame
                img_data['is table'] = util.detect_table(img_data['image'])
                if not img_data['is table']:
                    # hash and check if already exists
                    # note: we don't do this for tables because tables are
                    # almost always unique, even if their background frames are the same.
                    hash_img = np.ascontiguousarray(img_data['image'])
                    hash_img.flags.writeable = False
                    hasher = hashlib.md5()
                    hasher.update(hash_img.data)
                    img_hash = hasher.hexdigest()
                    
                    if img_hash in self.html_document.image_hashes:
                        continue
                    else:
                        self.html_document.image_hashes.add(img_hash)
                        
                img_bbox = img_data['bbox']
                x,y,w,h = img_bbox
                # convert position and size to match page coordinate system
                y += h
                y = img_orig_h_real - y
                
                x = img_orig_x + x * width_compression
                y = img_orig_y + y * height_compression
                w = w * width_compression
                h = h * height_compression
                
                img_data['bbox'] = (x, y, w, h)
                # get the center point of image on the page
                img_data['center'] = (x + w / 2.0, y + h / 2.0)
                
                img_data['fragmented'] = len(trimmed_images) > 1
                
                # convert to named tuple and store
                img_data = html_image(
                        image=img_data['image'], 
                        bbox=img_data['bbox'], 
                        is_table=img_data['is table'], 
                        center=img_data['center'], 
                        fragmented=img_data['fragmented']
                        )
                trimmed_images.append(img_data)
                
                
            images += trimmed_images
        
        
        # sort images based on their vertical position on the page
        images = sorted(images, key=lambda image: image.center[1], reverse=True)
        
        return images
    
    
    def _get_lines(self):
        """
        Gets a list of all (processed and raw) text lines identified in the page, stored
        as tuples with information about each line
        For more information see documentation for "lines" attribute
        """
        
        # list of all lines on the page
        lines = []
        # list of all raw text lines on the page
        raw_lines = []
        # container for all the page elements
        page_container_html = self.page_soup.find("div", class_="pc").contents
        
        
        for container in page_container_html:
            if 't' in container.attrs['class']:
                # the 't' class tells us the element is a line
                line_htmls = [container]
                x_offset, y_offset = 0, 0
            elif 'c' in container.attrs['class']:
                # the 'c' class tells us the element is an outer container
                # with lines inside it
                line_htmls = container.find_all("div", class_="t")
                x_offset, y_offset, _, _ = self.html_document.get_html_bbox_single(container)
            else:
                continue
                
            for line_html in line_htmls:
                # get the bounding box of the line
                line_x, line_y, line_w, line_h = self.html_document.get_html_bbox(line_html)
                # if no width provided, estimate width
                if line_w is None: line_w = self.page_width / 2.0
                
                if not line_x or not line_y or not line_w or not line_h:
                    continue
                
                line_x, line_y = line_x + x_offset, line_y + y_offset
                
                # get all text in the line
                line_text = util.get_descendent_text(line_html)
                raw_lines.append(line_text)
                
                # clean the text
                line_text_clean = util.clean_text(line_text)
                
                if line_text_clean.isspace() or line_text_clean == '':
                    continue
                
                # get maximum font size used in the line
                max_fs = self._get_max_fontsize(line_html)
                
                lines.append(html_line(
                    text=line_text_clean,
                    html=line_html,
                    center=(line_x + line_w / 2.0, line_y + line_h / 2.0),
                    bbox=(line_x, line_y, line_w, line_h),
                    max_font_size=max_fs
                ))                
    
        return lines, raw_lines
    
    def _get_text_lines(self):
        """
        Gets a list of strings representing the text on the page
        """
        text_lines = []
        for line in self.lines:
            text_lines.append(line.text)
        
        return text_lines
    
    
    def _get_max_fontsize(self, line_html):
        """
        Gets the maximum font-size used in a line.
        
        Parameters
        ----------
        line_html: bs4.element.Tag or bs4.element.NavigableString
            the line to extract the maximum font-size used
        
        Returns
        ----------
        float or None
            the maximum font-size used in the line, in pixels, or None if
            no font-size class found in tag
        """
        if type(line_html) != bs4.element.Tag:
            return None
        
        # get the font size of this element
        font_size = self.html_document.get_font_size(line_html)
        
        # get the maximum font sizes of this element's descendents
        child_max_fs = []
        for child in line_html.contents:
            child_font_size = self._get_max_fontsize(child)
            if child_font_size is not None:
                child_max_fs.append(child_font_size)
        
        # return the maximum font size of this element and this element's
        # descendents
        if font_size is not None:
            max_ = max([font_size] + child_max_fs)
        else:
            if len(child_max_fs) > 0:
                return max(child_max_fs)
            else:
                return None
        
        return max_
    
        