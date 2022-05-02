from gettext import find
from enum import Enum
import math
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

    # fix tilt
    img0 = img.crop((0,0, width, height))
    buffer = io.BytesIO()
    img0.save(buffer, "PNG")

    content = buffer.getvalue()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    text = response.full_text_annotation
    page = text.pages[0]

    vertices = page.blocks[0].bounding_box.vertices
    tilt_angle = math.atan2(vertices[3].y-vertices[2].y,vertices[2].x-vertices[3].x) * (180/math.pi)
    img = img.rotate(-tilt_angle)



    # image with NPI
    img1 = img.crop((width/1.35, height/6.3, width, height/5))
    buffer1 = io.BytesIO()
    img1.save(buffer1, "PNG")
    img1.show()

    content1 = buffer1.getvalue()

    image1 = vision.Image(content = content1)

    response1 = client.document_text_detection(image=image1)
    document1 = response1.full_text_annotation

    npi_number = document1.text.split()[1].split(')')[0]
    print(npi_number)


    #image with header
    # img2 = img.crop((0, height/3.1, width, height/2.7))
    # buffer2 = io.BytesIO()
    # img2.save(buffer2, "PNG")

    # content2 = buffer2.getvalue()

    # image2 = vision.Image(content=content2)
    

    # response2 = client.document_text_detection(image=image2)
    # document2 = response2.full_text_annotation

    # location_plan = find_word_location(document2, 'PLAN')
    # plan_text = text_within(document2, 10+location_plan.vertices[1].x, -5+location_plan.vertices[1].y, 800+location_plan.vertices[1].x, 5+location_plan.vertices[2].y)
    # print(plan_text)

    # location_client = find_word_location(document2, 'ID')
    # client_id = text_within(document2, 15+location_client.vertices[1].x, -5+location_client.vertices[1].y, 200+location_client.vertices[1].x, 5+location_client.vertices[2].y)
    # client_name = text_within(document2, 200+location_client.vertices[1].x, -5+location_client.vertices[1].y, 900+location_client.vertices[1].x, 5+location_client.vertices[2].y)
    # print(client_id)
    # print(client_name)

    # location_product = find_word_location(document2, 'PRODUCT')
    # product = text_within(document2, 15+location_product.vertices[1].x, -5+location_product.vertices[1].y, 900+location_product.vertices[1].x, 5+location_product.vertices[2].y)
    # print(product)

    # location_subclient = find_word_location(document2, 'SUBCLIENT')
    # subclient_id = text_within(document2, 15+location_subclient.vertices[1].x, -5+location_subclient.vertices[1].y, 200+location_subclient.vertices[1].x, 5+location_subclient.vertices[2].y)
    # subclient_name = text_within(document2, 200+location_subclient.vertices[1].x, -5+location_subclient.vertices[1].y, 900+location_subclient.vertices[1].x, 5+location_subclient.vertices[2].y)
    # print(subclient_id)
    # print(subclient_name)

    # img3 = img.crop((0, height/2.7, width, height/2.6))
    # buffer3 = io.BytesIO()
    # img3.save(buffer3, "PNG")

    # content3 = buffer3.getvalue()

    # image3 = vision.Image(content=content3)
    

    # response3 = client.document_text_detection(image=image3)
    # document3 = response3.full_text_annotation

    # location_network = find_word_location(document3, 'NETWORK')
    # network = text_within(document3, 15+location_network.vertices[1].x, -5+location_network.vertices[1].y, 400+location_network.vertices[1].x, 5+location_network.vertices[2].y)
    # print(network)

    # image of form data
    index = 0
    table_data = []
    while True:
        img4 = img.crop((0, height/2.55+index, width, height/2.45+index))
        buffer4 = io.BytesIO()
        img4.save(buffer4, "PNG")
        img4.show()

        content4 = buffer4.getvalue()

        image4 = vision.Image(content=content4)

        response4 = client.document_text_detection(image=image4)
        document4 = response4.full_text_annotation

        if document4.text == '':
            break
        else:
            text = document4.text.replace(' ', '\n')
            table_data.append(text.split())

            index += 50

    print(table_data)
    print('eef')





         




if __name__ == "__main__":
    main()