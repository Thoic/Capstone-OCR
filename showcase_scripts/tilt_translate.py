import math
from PIL import Image
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/3 degrees to right.jpg'

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


def main():
    client = vision.ImageAnnotatorClient()

    img = Image.open(IMAGE_PATH)
    width, height = img.size

    DENTIST_COPY_H = 0.0528787878788*height

    # fix tilt
    img0 = img.copy()
    buffer0 = io.BytesIO()
    img0.save(buffer0, "PNG")

    content0 = buffer0.getvalue()
    image0 = vision.Image(content=content0)

    response0 = client.text_detection(image=image0)
    document0 = response0.full_text_annotation
    page0 = document0.pages[0]

    vertices0 = page0.blocks[1].bounding_box.vertices
    tilt_angle = math.atan2(vertices0[3].y-vertices0[2].y,vertices0[2].x-vertices0[3].x) * (180/math.pi)
    img = img.rotate(-tilt_angle)

    # fix translate 
    img01 = img.crop((0, height/1.1, width, height))
    buffer01 = io.BytesIO()
    img01.save(buffer01, "PNG")

    content01 = buffer01.getvalue()
    image01 = vision.Image(content=content01)

    response01 = client.text_detection(image=image01)
    document01 = response01.full_text_annotation

    location_dentist = find_words_location(document01, 'Dentist Copy')

    dentist_midpointw = (location_dentist.vertices[2].x + location_dentist.vertices[3].x)/2
    doc_midpointw = width/2
    translatew = doc_midpointw - dentist_midpointw

    dentist_midpointh = (location_dentist.vertices[2].y + location_dentist.vertices[3].y)/2
    translateh = DENTIST_COPY_H - dentist_midpointh

    transform_mat = (1, 0, -translatew, 0, 1, -translateh)
    img = img.transform(size=(width, height), method=Image.AFFINE, data=transform_mat)

if __name__ == '__main__':
    main()