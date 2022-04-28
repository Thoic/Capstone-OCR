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


def main():
    client = vision.ImageAnnotatorClient()

    with io.open(IMAGE_PATH, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    location = find_word_location(document, 'PLAN')
    print(location)


if __name__ == "__main__":
    main()