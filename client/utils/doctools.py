#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Open and modify Microsoft Word 2007 docx files (called 'OpenXML' and 'Office OpenXML' by Microsoft)

Part of Python's docx module - http://github.com/mikemaccana/python-docx
See LICENSE for licensing information.
'''

from xml.etree import ElementTree as etree
import zipfile
import re
import os
import shutil
from os.path import join
import unicodedata

docx_nsprefixes = {
    # Text Content
    'mv':'urn:schemas-microsoft-com:mac:vml',
    'mo':'http://schemas.microsoft.com/office/mac/office/2008/main',
    've':'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'o':'urn:schemas-microsoft-com:office:office',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v':'urn:schemas-microsoft-com:vml',
    'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w10':'urn:schemas-microsoft-com:office:word',
    'wne':'http://schemas.microsoft.com/office/word/2006/wordml',
    # Drawing
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic':'http://schemas.openxmlformats.org/drawingml/2006/picture',
    # Properties (core and extended)
    'cp':"http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    'dc':"http://purl.org/dc/elements/1.1/",
    'dcterms':"http://purl.org/dc/terms/",
    'dcmitype':"http://purl.org/dc/dcmitype/",
    'xsi':"http://www.w3.org/2001/XMLSchema-instance",
    'ep':'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
    # Content Types (we're just making up our own namespaces here to save time)
    'ct':'http://schemas.openxmlformats.org/package/2006/content-types',
    # Package Relationships (we're just making up our own namespaces here to save time)
    'pr':'http://schemas.openxmlformats.org/package/2006/relationships'
    }

odt_nsprefixes = {
    'text':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
    }

def docx_open(file):
    '''Open a docx file, return a document XML tree'''
    doc = zipfile.ZipFile(file)
    xmlcontent = doc.read('word/document.xml')
    document = etree.fromstring(xmlcontent)
    return document

def docx_clean(document):
    """ Perform misc cleaning operations on documents.
        Returns cleaned document.
    """

    newdocument = document

    # Clean empty text and r tags
    for t in ('t', 'r'):
        rmlist = []
        for element in newdocument.getiterator():
            if element.tag == '{%s}%s' % (docx_nsprefixes['w'], t):
                if not element.text and not len(element):
                    rmlist.append(element)
        for element in rmlist:
            element.getparent().remove(element)

    return newdocument

def findTypeParent(element, tag):
    """ Finds fist parent of element of the given type
    
    @param object element: etree element
    @param string the tag parent to search for
    
    @return object element: the found parent or None when not found
    """
    
    p = element
    while True:
        p = p.getparent()
        if p.tag == tag:
            return p
    
    # Not found
    return None

def docx_replace(document,search,replace,bs=10):
    '''Replace all occurences of string with a different string, return updated document

    This is a modified version of python-docx.replace() that takes into
    account blocks of <bs> elements at a time. The replace element can also
    be a string or an xml etree element.

    What it does:
    It searches the entire document body for text blocks.
    Then scan thos text blocks for replace.
    Since the text to search could be spawned across multiple text blocks,
    we need to adopt some sort of algorithm to handle this situation.
    The smaller matching group of blocks (up to bs) is then adopted.
    If the matching group has more than one block, blocks other than first
    are cleared and all the replacement text is put on first block.

    Examples:
    original text blocks : [ 'Hel', 'lo,', ' world!' ]
    search / replace: 'Hello,' / 'Hi!'
    output blocks : [ 'Hi!', '', ' world!' ]

    original text blocks : [ 'Hel', 'lo,', ' world!' ]
    search / replace: 'Hello, world' / 'Hi!'
    output blocks : [ 'Hi!!', '', '' ]

    original text blocks : [ 'Hel', 'lo,', ' world!' ]
    search / replace: 'Hel' / 'Hal'
    output blocks : [ 'Hal', 'lo,', ' world!' ]

    @param instance  document: The original document
    @param str       search: The text to search for (regexp)
    @param mixed replace: The replacement text or lxml.etree element to
                          append, or a list of etree elements
    @param int       bs: See above

    @return instance The document with replacement applied

    '''

    newdocument = document

    # Compile the search regexp
    #searchre = re.compile(search)
    searchrearg = search
    if type(search) == 'unicode':
        searchrearg = unicodedata.normalize('NFC',search)
    searchre = re.compile(searchrearg)

    replaceNormalized = replace
    if isinstance(replace, dict):
        replaceNormalized = dict()
        for key in replace:
            if type(key) == 'unicode':
                replaceNormalized[unicodedata.normalize('NFC',key)] = replace[key]
            else:
                replaceNormalized[key] = replace[key]

    # Will match against searchels. Searchels is a list that contains last
    # n text elements found in the document. 1 < n < bs
    searchels = []

    for element in newdocument.getiterator():
        if element.tag == '{%s}t' % docx_nsprefixes['w']: # t (text) elements
            if element.text:
                # Add this element to searchels
                searchels.append(element)
                if len(searchels) > bs:
                    # Is searchels is too long, remove first elements
                    searchels.pop(0)

                # Search all combinations, of searchels, starting from
                # smaller up to bigger ones
                # l = search lenght
                # s = search start
                # e = element IDs to merge
                found = False
                for l in range(1,len(searchels)+1):
                    if found:
                        break
                    for s in range(len(searchels)):
                        if found:
                            break
                        if s+l <= len(searchels):
                            e = range(s,s+l)
                            txtsearch = ''
                            for k in e:
                                txtsearch += searchels[k].text

                            # Searcs for the text in the whole txtsearch
                            vars = None
                            if type(txtsearch) == 'unicode':
                                vars = searchre.finditer(unicodedata.normalize('NFC',txtsearch))
                            else:
                                vars = searchre.finditer(txtsearch)
                            for var in vars:
                                found = True
                                group = var.group()
                                curlen = 0
                                replacement = False
                                for i in e:
                                    curlen += len(searchels[i].text)
                                    if curlen > var.start() and not replacement:
                                        if isinstance(replace, dict):
                                            if group in replaceNormalized:
                                                #searchels[i].text = searchels[i].text.replace(group,replace[group])
                                                normalizedSearchel = searchels[i].text
                                                if type(normalizedSearchel) == 'unicode':
                                                    normalizedSearchel = unicodedata.normalize('NFC',normalizedSearchel)
                                                normalizedGroup = group[:len(normalizedSearchel)]
                                                if type(normalizedGroup) == 'unicode':
                                                    normalizedGroup = unicodedata.normalize('NFC',normalizedGroup)
                                                #searchels[i].text = normalizedSearchel.replace(normalizedGroup,replaceNormalized[normalizedGroup])
                                                replacement = replaceNormalized[group]
                                                replacement = replacement.replace('\r\n','LINEBREAKHERE')
                                                replacement = replacement.replace('\r','LINEBREAKHERE')
                                                replacement = replacement.replace('\n','LINEBREAKHERE')
                                                #searchels[i].text = normalizedSearchel.replace(normalizedGroup,replaceNormalized[normalizedGroup])
                                                searchels[i].text = normalizedSearchel.replace(normalizedGroup,replacement)
                                        else:
                                            #searchels[i].text = searchels[i].text.replace(group,replace)
                                            normalizedSearchel = searchels[i].text
                                            if type(normalizedSearchel) == 'unicode':
                                                normalizedSearchel = unicodedata.normalize('NFC',normalizedSearchel)
                                            normalizedGroup = group[:len(normalizedSearchel)]
                                            if type(normalizedGroup) == 'unicode':
                                                normalizedGroup = unicodedata.normalize('NFC',normalizedGroup)
                                            #normalizedSearchel = searchels[i].text
                                            #if type(searchels[i].text) == 'unicode':
                                            #    normalizedSearchel = unicodedata.normalize('NFC',searchels[i].text)
                                            #searchels[i].text = normalizedSearchel.replace(group[:len(normalizedSearchel)],replaceNormalized)
                                            replacement = replaceNormalized
                                            replacement = replacement.replace('\r\n','LINEBREAKHERE')
                                            replacement = replacement.replace('\r','LINEBREAKHERE')
                                            replacement = replacement.replace('\n','LINEBREAKHERE')
                                            #searchels[i].text = normalizedSearchel.replace(normalizedGroup,replaceNormalized)
                                            searchels[i].text = normalizedSearchel.replace(normalizedGroup,replacement)
                                        replacement = True
                                    else:
                                        # Clears the other text elements
                                        searchels[i].text = ''
    return newdocument

def docx_save(document,inputfile,outputfile):
    #inputdoc = shutil.copyfile(inputfile,outputfile)
    #outputdoc = zipfile.ZipFile(outputfile,mode='a',compression=zipfile.ZIP_DEFLATED)
    ##outputdoc.writestr('word/document.xml',etree.tostring(document,'ascii'))
    #outputdoc.writestr('word/document.xml',etree.tostring(document,'utf-8'))
    #outputdoc.close()
    zin = zipfile.ZipFile(inputfile,'r')
    zout = zipfile.ZipFile(outputfile,'w')
    for item in zin.infolist():
        buffer = zin.read(item.filename)
        if item.filename not in ['document.xml','word/document.xml']:
            zout.writestr(item,buffer)
        else:
            documentString = etree.tostring(document,'utf-8')
            documentString = documentString.replace('LINEBREAKHERE','</ns0:t><ns0:br/><ns0:t>')
            documentString = documentString.replace('&amp;#','&#')
            #zout.writestr('word/document.xml',etree.tostring(document,'utf-8'))
            zout.writestr('word/document.xml',documentString)
    zout.close()
    zout.close()
    zin.close()




def odt_open(file):
    doc = zipfile.ZipFile(file)
    xmlcontent = doc.read('content.xml')
    document = etree.fromstring(xmlcontent)
    return document

def odt_save(document,inputfile,outputfile):
    #inputdoc = shutil.copyfile(inputfile,outputfile)
    #outputdoc = zipfile.ZipFile(outputfile,mode='a',compression=zipfile.ZIP_DEFLATED)
    ##outputdoc.writestr('content.xml',etree.tostring(document,'ascii'))
    #outputdoc.writestr('content.xml',etree.tostring(document,'utf-8'))
    #outputdoc.close()
    zin = zipfile.ZipFile(inputfile,'r')
    zout = zipfile.ZipFile(outputfile,'w')
    for item in zin.infolist():
        buffer = zin.read(item.filename)
        if item.filename != 'content.xml':
            zout.writestr(item,buffer)
        else:
            documentString = etree.tostring(document,'utf-8')
            documentString = documentString.replace('LINEBREAKHERE','<ns1:line-break/>')
            documentString = documentString.replace('&amp;#','&#')
            zout.writestr('content.xml',documentString)
    zout.close()
    zout.close()
    zin.close()

def odt_replace(document,search,replace, bs=10):
    newdocument = document
   
    searchrearg = search
    if type(search) == 'unicode':
        searchrearg = unicodedata.normalize('NFC',search)
    searchre = re.compile(searchrearg)
    
    replaceNormalized = replace
    if isinstance(replace, dict):
        replaceNormalized = dict()
        for key in replace:
            normalizedKey = key
            if type(key) == 'unicode':
                normalizedKey = unicodedata.normalize('NFC',key)
            replaceNormalized[normalizedKey] = replace[key]
    
    searchels = []
    
    for element in newdocument.getiterator():
        if odt_nsprefixes['text'] in  element.tag:
            if element.text:
                
                searchels.append(element)
                if len(searchels) > bs:
                    # Is searchels is too long, remove first elements
                    searchels.pop(0)
                
                found = False
                for l in range(1,len(searchels)+1):
                    if found:
                        break
                    for s in range(len(searchels)):
                        if found:
                            break
                        if s+l <= len(searchels):
                            e = range(s,s+l)
                            txtsearch = ''
                            for k in e:
                                txtsearch += searchels[k].text

                            # Searcs for the text in the whole txtsearch
                            vars = None
                            if type(txtsearch) == 'unicode':
                                vars = searchre.finditer(unicodedata.normalize('NFC',txtsearch))
                            else:
                                vars = searchre.finditer(txtsearch)

                            for var in vars:
                                    
                                found = True
                                group = var.group()
                                curlen = 0
                                replacement = False
                                for i in e:
                                    curlen += len(searchels[i].text)
                                    if curlen > var.start() and not replacement:
                                        if isinstance(replace, dict):
                                            if group in replaceNormalized:
                                                #searchels[i].text = searchels[i].text.replace(group,replace[group])
                                                normalizedSearchel = searchels[i].text
                                                if type(normalizedSearchel) == 'unicode':
                                                    normalizedSearchel = unicodedata.normalize('NFC',normalizedSearchel)
                                                normalizedGroup = group[:len(normalizedSearchel)]
                                                if type(normalizedGroup) == 'unicode':
                                                    normalizedGroup = unicodedata.normalize('NFC',normalizedGroup)

                                                #searchels[i].text = normalizedSearchel.replace(normalizedGroup,replaceNormalized[normalizedGroup])
                                                replacement = replaceNormalized[group]
                                                replacement = replacement.replace('\r\n','LINEBREAKHERE')
                                                replacement = replacement.replace('\r','LINEBREAKHERE')
                                                replacement = replacement.replace('\n','LINEBREAKHERE')
                                                #searchels[i].text = normalizedSearchel.replace(normalizedGroup,replaceNormalized[normalizedGroup])
                                                searchels[i].text = normalizedSearchel.replace(normalizedGroup,replacement)
                                        else:
                                            #searchels[i].text = searchels[i].text.replace(group,replace)
                                            normalizedSearchel = searchels[i].text
                                            if type(normalizedSearchel) == 'unicode':
                                                normalizedSearchel = unicodedata.normalize('NFC',normalizedSearchel)
                                            normalizedGroup = group[:len(normalizedSearchel)]
                                            if type(normalizedGroup) == 'unicode':
                                                normalizedGroup = unicodedata.normalize('NFC',normalizedGroup)
                                            #normalizedSearchel = searchels[i].text
                                            #if type(searchels[i].text) == 'unicode':
                                            #    normalizedSearchel = unicodedata.normalize('NFC',searchels[i].text)
                                            #searchels[i].text = normalizedSearchel.replace(group[:len(normalizedSearchel)],replaceNormalized)
                                            replacement = replaceNormalized
                                            replacement = replacement.replace('\r\n','LINEBREAKHERE')
                                            replacement = replacement.replace('\r','LINEBREAKHERE')
                                            replacement = replacement.replace('\n','LINEBREAKHERE')
                                            #searchels[i].text = normalizedSearchel.replace(normalizedGroup,replaceNormalized)
                                            searchels[i].text = normalizedSearchel.replace(normalizedGroup,replacement)
                                        replacement = True
                                    else:
                                        # Clears the other text elements
                                        searchels[i].text = ''
    return newdocument


def unxmlrefchar(text):
    if type(text) == unicode:
        try:
            text.encode('ascii')
        except:
            text = text.encode('ascii','xmlcharrefreplace')
    return etree.fromstring('<foo>'+text+'</foo>').text

def rtfencode(text):
    outtextList = []
    for c in text:
        if ord(c) <= 0x7f:
            outtextList.append(c)
        else:
            outtextList.append('\\u'+str(ord(c))+'?')
    return u''.join(outtextList)

def rtf_open(file):
    doc = open(file,'rb')
    content = doc.read()
    doc.close()
    return content

def rtf_save(document,outputfile):
    doc = open(outputfile,'wb')
    doc.write(document) 
    #if (type(document) == unicode):
    #    document = unicodedata.normalize('NFKD', document).encode('ascii','ignore')    
    #doc.write(document)
    doc.close()

def rtf_replace(document,search,replace):
    newdocument = document
    searchre = re.compile(search)
    vars = searchre.finditer(newdocument)
    
    for var in vars:
        group = var.group()
        if isinstance(replace, dict):
            if group in replace:
                #newdocument = b'%s' % newdocument.replace(group,replace[group])
                replacement = replace[group]
                print replacement
                
                #replacement = unxmlrefchar(replacement).encode('utf-16')
                #replacement = unxmlrefchar(replacement).encode('latin1')
                if '<' in replacement:
                    replacement = replacement.replace('<', '&lt;')
                replacement = rtfencode(unxmlrefchar(replacement))
                replacement = replacement.replace('\r\n','\\par ')
                replacement = replacement.replace('\r','\\par ')
                replacement = replacement.replace('\n','\\par ')
                newdocument = b'%s' % newdocument.replace(group,replacement)
        else:
            replacement = replace
            #replacement = unxmlrefchar(replacement).encode('utf-16')
            #replacement = unxmlrefchar(replacement).encode('latin1')
            if '<' in replacement:
                replacement = replacement.replace('<', '&lt;')
            replacement = rtfencode(unxmlrefchar(replacement))
            replacement = replacement.replace('\r\n','\\par ')
            replacement = replacement.replace('\r','\\par ')
            replacement = replacement.replace('\n','\\par ')
            newdocument = b'%s' % newdocument.replace(group,replacement)
            #newdocument = b'%s' % newdocument.replace(group,replace)
    return newdocument

