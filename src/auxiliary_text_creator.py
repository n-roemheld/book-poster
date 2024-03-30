from PIL import Image


class Auxiliary_text_creator:
    def __init__(self, layout, config) -> None:
        self.layout = layout
        self.config = config

    def add_title(self, draw):
        title_position = self.layout.get_title_position()
        draw.text(
            title_position.dim_px,
            self.config.get_title_str(),
            font=self.layout.title.font,
            fill="black",
            anchor="ma",
        )

    def add_right_signature(self, poster_image, draw):
        signature_text_position = self.layout.get_signature_text_position_right()
        signature_qr_code_position = self.layout.get_signature_position_right()
        draw.text(
            signature_text_position.xy_px,
            self.config.credit_str,
            font=self.layout.signature.font,
            fill="black",
            align="right",
            anchor="rm",
        )
        qr_code = self.create_qr_code(
            self.config.credit_url, self.layout.get_qr_code_size().dim_px[0]
        )
        poster_image.paste(qr_code, signature_qr_code_position.xy_px)

    def add_left_signature(self, user_profile_link, poster_image, draw, user_name="me"):
        signature_str = f"Follow {user_name} on Goodreads!"
        signature_text_position = self.layout.get_signature_text_position_left()
        signature_qr_code_position = self.layout.get_signature_position_left()
        draw.text(
            signature_text_position.xy_px,
            signature_str,
            font=self.layout.signature.font,
            fill="black",
            align="left",
            anchor="lm",
        )
        qr_code = self.create_qr_code(
            user_profile_link, self.layout.get_qr_code_size().dim_px[0]
        )
        poster_image.paste(qr_code, signature_qr_code_position.xy_px)

    def create_qr_code(self, link: str, size_px: int) -> Image:
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            box_size=1,
            border=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
        )
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        return img.resize((size_px, size_px), Image.BICUBIC)