from gettext import find
from enum import Enum
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

    with io.open(IMAGE_PATH, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    locationMich = find_word_location(document, 'MICHIGAN')
    location = find_word_location(document, 'PLAN')
    print('loc plan:')
    print(location)
    print('loc michigan:')
    print(locationMich)
    text = text_within(document, 10+location.vertices[1].x, -15+location.vertices[1].y, 800+location.vertices[1].x, 10+location.vertices[2].y)
    print(text)


if __name__ == "__main__":
    main()