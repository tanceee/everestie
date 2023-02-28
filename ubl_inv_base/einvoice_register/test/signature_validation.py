from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import b64decode

XML_SIG_METHOD = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
XML_SCHEMA_NS = "https://eFiskalizimi.tatime.gov.al/FiscalizationService/schema"
XML_REQUEST_ELEMENT = "RegisterInvoiceRequest"
XML_REQUEST_ID = "Request"
REQUEST_TO_SIGN = ''


def verify_sign(public_key_loc, signature, data):
    """
    Verifies with a public key from whom the data came that it was indeed signed by their private key
    param: public_key_loc Path to public key
    param: signature String signature to be verified
    return: Boolean. True if the signature is valid; False otherwise.
    """
    pub_key = open(public_key_loc, "r").read()
    rsa_key = RSA.importKey(pub_key)
    signer = PKCS1_v1_5.new(rsa_key)
    digest = SHA256.new()
    # Assumes the data is base64 encoded to begin with
    digest.update(b64decode(data))
    if signer.verify(digest, b64decode(signature)):
        return True
    return False


verify_sign('/home/ardit/PycharmProjects/fiscalization/MASTERIT.p12', XML_SIG_METHOD)
