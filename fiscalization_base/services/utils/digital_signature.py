import signxml
from OpenSSL import crypto
from signxml import XMLSigner


def sign_xml(xml_to_sign, company_p12_certificate, certificate_password):
    # certificate = os.getenv('P12_LOCATION')
    # password = os.getenv('PRIVATE_PASSWORD').encode('utf-8')
    p12 = crypto.load_pkcs12(company_p12_certificate, certificate_password)
    cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                         p12.get_privatekey())

    signed_root = XMLSigner(method=signxml.methods.enveloped,
                            signature_algorithm='rsa-sha256',
                            digest_algorithm='sha256',
                            c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#').sign(
        xml_to_sign,
        key=private_key, cert=cert, id_attribute='Request')

    return signed_root
