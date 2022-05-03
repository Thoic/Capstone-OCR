import math
from PIL import Image
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/center'
IMAGE_PATH2 = 'dataset/extreme low'

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

def assemble_words(paragraph):
    assembled_words=''
    for word in paragraph.words:
        assembled_word=''
        for symbol in word.symbols:
            assembled_word += symbol.text
        assembled_words += assembled_word + ' '
    return assembled_words.strip()

def find_words_location(document, words_to_find):
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                assembled_words = assemble_words(paragraph)
                if (assembled_words == words_to_find):
                    return paragraph.bounding_box

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

    img = Image.open(IMAGE_PATH + '.jpg')

    width, height = img.size

    DENTIST_COPY_H = 0.0528787878788*height

    # fix translate 
    img0 = img.crop((0, height/1.1, width, height))
    buffer = io.BytesIO()
    img0.save(buffer, "PNG")

    content = buffer.getvalue()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    document = response.full_text_annotation

    location_dentist = find_words_location(document, 'Dentist Copy')

    dentist_midpointw = (location_dentist.vertices[2].x + location_dentist.vertices[3].x)/2
    doc_midpointw = width/2
    translatew = doc_midpointw - dentist_midpointw

    dentist_midpointh = (location_dentist.vertices[2].y + location_dentist.vertices[3].y)/2
    translateh = DENTIST_COPY_H - dentist_midpointh

    transform_mat = (1, 0, -translatew, 0, 1, -translateh)
    img = img.transform(size=(width, height), method=Image.AFFINE, data=transform_mat)
    img.show()

    img_second = Image.open(IMAGE_PATH2 + '.jpg')

    width_second, height_second = img_second.size

    # fix translate second
    img_second0 = img_second.crop((0, height_second/1.1, width_second, height_second))
    buffer_second = io.BytesIO()
    img_second0.save(buffer_second, "PNG")

    content_second = buffer_second.getvalue()
    image_second = vision.Image(content=content_second)

    response_second = client.text_detection(image=image_second)
    document_second = response_second.full_text_annotation

    location_second_dentist = find_words_location(document_second, 'Dentist Copy')

    dentist_second_midpointw = (location_second_dentist.vertices[2].x + location_second_dentist.vertices[3].x)/2
    doc_second_midpointw = width_second/2
    translate_secondw = doc_second_midpointw - dentist_second_midpointw

    dentist_second_midpointh = (location_second_dentist.vertices[2].y + location_second_dentist.vertices[3].y)/2
    translate_secondh = DENTIST_COPY_H - dentist_second_midpointh

    transform_second_mat = (1, 0, -translate_secondw, 0, 1, -translate_secondh)
    img_second = img_second.transform(size=(width_second, height_second), method=Image.AFFINE, data=transform_second_mat)
    img_second.show()

if __name__ == "__main__":
    main()