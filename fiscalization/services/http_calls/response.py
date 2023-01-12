from lxml import etree
import logging

_logger = logging.getLogger(__name__)
SUCCESS_TAGS = ('FIC', 'TCRCode', 'FCDC', 'FWTNIC')
ERROR_TAG = 'faultstring'


def parse_response(response):
    if isinstance(response, bytes):
        response = response.decode('utf-8')
    try:
        root = etree.fromstring(response)
    except etree.XMLSyntaxError as e:
        _logger.error("\nXML Syntax Error: %s" % e)
        return None

    for el in root.iter():
        for tag in SUCCESS_TAGS:
            if tag in el.tag:
                return el.text
        if ERROR_TAG in el.tag:
            return {'Error': el.text}
    return None
