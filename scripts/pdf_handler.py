# -*- coding: utf-8 -*-
import PyPDF2
import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


class PDFHandler(object):
    def __init__(self, input_file):
        self.input_file = input_file
        self.input_file_handler = open(self.input_file, "rb")
        self.input_stream = PyPDF2.PdfFileReader(self.input_file_handler)
        self.dependent_handlers = []

    def save(self, output_file):
        output = PyPDF2.PdfFileWriter()
        for i in range(self.input_stream.getNumPages()):
            output.addPage(self.input_stream.getPage(i))
        if not output_file:
            output_file = self.input_file

        with open(output_file, "wb") as output_stream:
            output.write(output_stream)

        for file_handler in self.dependent_handlers:
            file_handler.close()
        self.input_file_handler.close()

    def merge_page(
        self, page_path, page_number=0, scale=1.0, tx=0, ty=0, last_page=False
    ):
        if page_number and last_page:
            raise ValueError(
                "You must pass either page_number or last_page to the function"
            )

        if last_page:
            page_number = self.input_stream.getNumPages() - 1

        file_handler = open(page_path, "rb")
        self.dependent_handlers.append(file_handler)

        page_for_merge = PyPDF2.PdfFileReader(file_handler)

        input_page = self.input_stream.getPage(page_number)
        input_page.mergeScaledTranslatedPage(page_for_merge.getPage(0), scale, tx, ty)

    def add_label(
        self, text, page_number=0, tx=0, ty=0, last_page=False, font_config=None
    ):
        if page_number and last_page:
            raise ValueError(
                "You must pass either page_number or last_page to the function"
            )
        if not isinstance(font_config, dict):
            font_config = {}

        if last_page:
            page_number = self.input_stream.getNumPages() - 1

        packet = StringIO.StringIO()
        c = canvas.Canvas(packet, pagesize=letter)

        if any(["red" in font_config, "green" in font_config, "blue" in font_config]):
            c.setFillColorRGB(
                float(font_config.get("red", 0)) / 256,
                float(font_config.get("green", 0)) / 256,
                float(font_config.get("blue", 0)) / 256,
            )

        if any(["font" in font_config, "font_size" in font_config]):
            font = font_config.get("font", "Helvetica")
            available_fonts = c.getAvailableFonts()
            if font not in available_fonts:
                raise ValueError(
                    "Cannot set font {font}. Available fonts: {available_fonts}".format(
                        font=font, available_fonts=available_fonts
                    )
                )

            c.setFont(font, font_config.get("font_size", 14))

        c.drawString(tx, ty, text)
        c.save()

        packet.seek(0)
        label_pdf = PyPDF2.PdfFileReader(packet)
        page = self.input_stream.getPage(page_number)
        page.mergePage(label_pdf.getPage(0))
