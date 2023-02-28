from Crypto.Hash import SHA256, MD5
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from OpenSSL import crypto


def build_wtnic_input(issuer_nuis, datetime_created, wtn_number, business_unit_code, soft_code):
    return issuer_nuis + '|' + datetime_created + '|' + wtn_number + '|' + business_unit_code + '|' + soft_code


def generate_wtnic_signature(wtnic_input, company_p12_certificate, certificate_password):
    message = wtnic_input.encode('utf-8')
    p12 = crypto.load_pkcs12(company_p12_certificate, certificate_password)
    key_bytes = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
    key = RSA.import_key(key_bytes)
    h = SHA256.new(message)
    signer = PKCS1_v1_5.new(key)
    signature = signer.sign(h)
    return str(signature.hex()).upper()


def generate_wtnic(wtnic_input, company_p12_certificate, certificate_password):
    message = wtnic_input.encode('utf-8')
    p12 = crypto.load_pkcs12(company_p12_certificate, certificate_password)
    key_bytes = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
    key = RSA.import_key(key_bytes)
    h = SHA256.new(message)
    signer = PKCS1_v1_5.new(key)
    signature = signer.sign(h)
    md5_digest = MD5.new(signature)
    return str(md5_digest.digest().hex()).upper()
