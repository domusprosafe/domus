from xml.sax.saxutils import quoteattr
import re

def psXMLToXML(text):
    rawstr = r"""'''(.*?)'''"""
    codeRe = re.compile(rawstr, re.IGNORECASE|re.DOTALL)
    vars = codeRe.finditer(text)
    for var in vars:
        code = str(var.group())
        splitCode = code[3:-3].split('\n')
        indent = min([len(el)-len(el.lstrip()) for el in splitCode if el.strip()])
        unindentedCode = '\n'.join([el[indent:] for el in splitCode if el.strip()])
        xmlCode = quoteattr(unindentedCode)
        text = text.replace(code,xmlCode[1:-1])
    return text

if __name__=='__main__':

    import sys
    
    f = open(sys.argv[1],'rb')
    text = f.read()
    f.close()
    
    text = psXMLToXML(text)

    print text
    #from xml.etree import ElementTree as etree
    #print etree.fromstring(text)
   
    #if len(sys.argv) > 2: 
    #    f = open(sys.argv[2],'wb')
    #    f.write(text)
    #    f.close()

