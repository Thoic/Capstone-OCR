from gettext import find
from enum import Enum
from PIL import Image
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/original2.jpg'

def assemble_word(word):
    assembled_word=""
    for symbol in word.symbols:
        assembled_word += symbol.text
    return assembled_word

def find_word_location(document, word_to_find):
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    assembled_word = assemble_word(word)
                    if(assembled_word == word_to_find):
                        return word.bounding_box

def text_within(document, x1, y1, x2, y2) -> str:
    text = ''
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        min_x = min(symbol.bounding_box.vertices[0].x, symbol.bounding_box.vertices[1].x,
                            symbol.bounding_box.vertices[2].x, symbol.bounding_box.vertices[3].x)
                        max_x = max(symbol.bounding_box.vertices[0].x, symbol.bounding_box.vertices[1].x,
                            symbol.bounding_box.vertices[2].x, symbol.bounding_box.vertices[3].x)
                        min_y = min(symbol.bounding_box.vertices[0].y, symbol.bounding_box.vertices[1].y,
                            symbol.bounding_box.vertices[2].y, symbol.bounding_box.vertices[3].y)
                        max_y = max(symbol.bounding_box.vertices[0].y, symbol.bounding_box.vertices[1].y,
                            symbol.bounding_box.vertices[2].y, symbol.bounding_box.vertices[3].y)
                        if (min_x >= x1 and max_x <= x2 and min_y >= y1 and max_y <= y2):
                            text += symbol.text
                            if (symbol.property.detected_break.type == 1 or
                                symbol.property.detected_break.type == 3):
                                text += ' '
                            if (symbol.property.detected_break.type == 2):
                                text += '\t'
                            if (symbol.property.detected_break.type == 5):
                                text+='\n'
    return text

def main():
    client = vision.ImageAnnotatorClient()

    img = Image.open(IMAGE_PATH)

    width, height = img.size

    #image with NPI
    img1 = img.crop((width/1.5, height/7, width, height/5))
    buffer1 = io.BytesIO()
    img1.save(buffer1, "PNG")

    content1 = buffer1.getvalue()

    image1 = vision.Image(content = content1)

    response1 = client.document_text_detection(image=image1)
    document1 = response1.full_text_annotation

    location_npi = find_word_location(document1, 'NPI')
    npi_text = text_within(document1, 20+location_npi.vertices[1].x, -10+location_npi.vertices[1].y, 235+location_npi.vertices[1].x, 10+location_npi.vertices[2].y)
    print(npi_text)


    #image with form data
    img2 = img.crop((0, height/4, width, height/2))
    buffer2 = io.BytesIO()
    img2.save(buffer2, "PNG")
    img2.show()

    content2 = buffer2.getvalue()

    image2 = vision.Image(content=content2)
    

    response2 = client.document_text_detection(image=image2)
    document2 = response2.full_text_annotation

    location = find_word_location(document2, 'PLAN')
    plan_text = text_within(document2, 10+location.vertices[1].x, -15+location.vertices[1].y, 800+location.vertices[1].x, 10+location.vertices[2].y)


if __name__ == "__main__":
    main()