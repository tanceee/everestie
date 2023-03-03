import qrcode
from io import BytesIO

import base64

def make_invoice_qr_code(inv_check_api_endpoint,
        invoice_iic, invoice_issuer_nuis, invoice_issue_date_time,
        invoice_inv_ord_num,
        invoice_busin_unit_code, invoice_tcr_code, invoice_soft_code,
        invoice_tot_price
):
    qr = qrcode.QRCode(
        version=1,
        # error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=5,
    )
    print("11111111111",invoice_tot_price)
    qr.add_data(
        inv_check_api_endpoint +
        "?iic=" + invoice_iic +
        "&tin=" + invoice_issuer_nuis +
        "&crtd=" + invoice_issue_date_time +
        "&ord=" + invoice_inv_ord_num +
        "&bu=" + invoice_busin_unit_code +
        "&cr=" + invoice_tcr_code +
        "&sw=" + invoice_soft_code +
        "&prc=" + invoice_tot_price
    )
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_image = base64.b64encode(temp.getvalue())
    return qr_image

