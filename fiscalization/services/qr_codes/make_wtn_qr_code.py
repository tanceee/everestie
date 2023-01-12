import qrcode

def make_wtn_qr_code(
        wtn_wtnic,  wtn_issuer_nuis, wtn_issue_date_time, wtn_wtn_ord_num,
        wtn_busin_unit_code, wtn_soft_code
    ):

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )

    qr.add_data(
        "https://efiskalizimi-app-test.tatime.gov.al/invoice-check/#/wtn" +
        "?wtnic=" + wtn_wtnic +
        "&tin=" + wtn_issuer_nuis +
        "&crtd=" + wtn_issue_date_time +
        "&ord=" +   wtn_wtn_ord_num  +
        "&bu=" + wtn_busin_unit_code +
        "&sw=" + wtn_soft_code
    )
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    img.save("qr_codes/wtn_qr_code.png")

    return img