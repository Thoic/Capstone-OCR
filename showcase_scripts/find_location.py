from gettext import find
from enum import Enum
import math
from PIL import Image
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/center.jpg'

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

    # fix tilt
    img0 = img.copy()
    buffer = io.BytesIO()
    img0.save(buffer, "PNG")

    content = buffer.getvalue()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    text = response.full_text_annotation
    page = text.pages[0]

    vertices = page.blocks[1].bounding_box.vertices
    tilt_angle = math.atan2(vertices[3].y-vertices[2].y,vertices[2].x-vertices[3].x) * (180/math.pi)
    img = img.rotate(-tilt_angle)

    width, height = img.size


    # image with NPI
    # img1 = img.crop((width/1.8, height/8, width, height/5))
    # buffer1 = io.BytesIO()
    # img1.save(buffer1, "PNG")

    # content1 = buffer1.getvalue()

    # image1 = vision.Image(content = content1)

    # response1 = client.document_text_detection(image=image1)
    # document1 = response1.full_text_annotation

    # location_npi = find_word_location(document1, 'NPI')
    # npi_text = text_within(document1, 15+location_npi.vertices[1].x, -5+location_npi.vertices[1].y, 245 + location_npi.vertices[1].x, 5+location_npi.vertices[2].y)
    # print(npi_text)


    #image with header left side
    # img2 = img.crop((0, height/3.15, width/2, height/2.75))
    # buffer2 = io.BytesIO()
    # img2.save(buffer2, "PNG")

    # content2 = buffer2.getvalue()

    # image2 = vision.Image(content=content2)

    # response2 = client.document_text_detection(image=image2)
    # document2 = response2.full_text_annotation

    # location_plan = find_word_location(document2, 'PLAN')
    # plan_text = text_within(document2, 10+location_plan.vertices[1].x, -5+location_plan.vertices[1].y, width/2, 5+location_plan.vertices[2].y)
    # plan_text = plan_text.strip()
    # print(plan_text)

    # location_client = find_word_location(document2, 'ID')
    # client_id = text_within(document2, 15+location_client.vertices[1].x, -5+location_client.vertices[1].y, 200+location_client.vertices[1].x, 5+location_client.vertices[2].y)
    # client_name = text_within(document2, 200+location_client.vertices[1].x, -5+location_client.vertices[1].y, width/2, 5+location_client.vertices[2].y)
    # client_id = client_id.strip()
    # client_name = client_name.strip()
    # print(client_id)
    # print(client_name)

    # location_subclient = find_word_location(document2, 'SUBCLIENT')
    # subclient_id = text_within(document2, 15+location_subclient.vertices[1].x, -5+location_subclient.vertices[1].y, 200+location_subclient.vertices[1].x, 5+location_subclient.vertices[2].y)
    # subclient_name = text_within(document2, 200+location_subclient.vertices[1].x, -5+location_subclient.vertices[1].y, width/2, 5+location_subclient.vertices[2].y)
    # subclient_id = subclient_id.strip()
    # subclient_name = subclient_name.strip()
    # print(subclient_id)
    # print(subclient_name)

    
    # image with header right side
    # img3 = img.crop((width/2, height/3.15, width, height/2.75))
    # buffer3 = io.BytesIO()
    # img3.save(buffer3, "PNG")

    # content3 = buffer.getvalue()

    # image3 = vision.Image(content=content3)

    # response3 = client.document_text_detection(image=image3)
    # document3 = response3.full_text_annotation

    # location_product = find_word_location(document3, 'PRODUCT')
    # product_text = text_within(document3, 10+location_product.vertices[1].x, -5+location_product.vertices[1].y, width, 5+location_product.vertices[2].y)
    # product_text = product_text.strip()
    # print(product_text)

    # image below header
    # img4 = img.crop((0, height/2.8, width/2, height/2.6))
    # buffer4 = io.BytesIO()
    # img4.save(buffer4, "PNG")

    # content4 = buffer4.getvalue()

    # image4 = vision.Image(content=content4)

    # response4 = client.document_text_detection(image=image4)
    # document4 = response4.full_text_annotation

    # location_network = find_word_location(document3, 'NETWORK')
    # network_name = text_within(document3, 15+location_network.vertices[1].x, -5+location_network.vertices[1].y, width/2, 5+location_network.vertices[2].y)
    # network_name = network_name.strip()
    # print(network_name)

    # image of form data
    table_data = []
    img5 = img.crop((0, height/2.7, width, height/1.7))
    buffer5 = io.BytesIO()
    img5.save(buffer5, "PNG")

    content5 = buffer5.getvalue()

    image5 = vision.Image(content=content5)

    response5 = client.document_text_detection(image=image5)
    document5 = response5.full_text_annotation

    table_string = document5.text.strip()
    raw_table = table_string.split('\n')
    num_entries = len(raw_table)//10

    for i in range(num_entries):
        table_data.append((raw_table[i],
                            raw_table[num_entries+i],
                            raw_table[2*num_entries+i],
                            raw_table[3*num_entries+i],
                            raw_table[4*num_entries+i],
                            raw_table[5*num_entries+i],
                            raw_table[6*num_entries+i],
                            raw_table[7*num_entries+i],
                            raw_table[8*num_entries+i],
                            raw_table[9*num_entries+i]))
    print(table_data)


if __name__ == "__main__":
    main()