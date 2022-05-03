import math
from PIL import Image
import io
import json

from google.cloud import vision

IMAGE_PATH = 'dataset/center.jpg'
JSON_PATH = 'dataset/json_data.json'

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
    img_temp = img.copy()
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    text = response.full_text_annotation
    page = text.pages[0]

    vertices = page.blocks[1].bounding_box.vertices
    tilt_angle = math.atan2(vertices[3].y-vertices[2].y,vertices[2].x-vertices[3].x) * (180/math.pi)
    img = img.rotate(-tilt_angle)

    # fix translate 
    img_temp = img.crop((0, height/1.1, width, height))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

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
    img = img.transform(size=(width, height), method=Image.Transform.AFFINE, data=transform_mat)

    # image for NPI
    img_temp = img.crop((width/1.4, height/6.3, width, height/5))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content = content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    npi_number = document.text.split()[1].split(')')[0]
    print(f'npi_number: {npi_number}')


    # image for plan
    img_temp = img.crop((0, height/3.15, width/2, height/3))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)
    
    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    plan_name = document.text.split(':')[1].strip()
    print(f'plan_name: {plan_name}')

    # image for product
    img_temp = img.crop((width/2, height/3.15, width, height/3))
    buffer = io.BytesIO()
    img_temp.save(buffer, 'PNG')

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    product_name = document.text.split(':')[1].strip()
    print(f'product_name: {product_name}')

    # image for client/id
    img_temp = img.crop((0, height/3.05, width/2, height/2.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)
    
    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    client_idname = document.text.split(':')[1].strip().split('\n')
    client_id = client_idname[0]
    client_name = client_idname[1]
    print(f'client_id,client_name: {client_id}, {client_name}')

    # image for subclient
    img_temp = img.crop((0, height/2.95, width/2, height/2.8))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)
    
    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    subclient = document.text.split(':')[1].strip().split('\n')
    subclient_id = subclient[0]
    subclient_name = subclient[1]
    print(f'subclient_id,subclient_name: {subclient_id}, {subclient_name}')

    # image for network
    img_temp = img.crop((0, height/2.8, width/2, height/2.65))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)
    
    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    network = document.text.split(':')[1].strip()
    print(f'network: {network}')

    # image of form data
    index = 0
    table_data = []
    table_labels = ['date', 'procedure_code', 'submitted_amount', 'max_approved_fee', 'allowed_amount', 'co-pay', 'payment']
    while True:
        img_temp = img.crop((0, height/2.6+index, width, height/2.5+index))
        buffer = io.BytesIO()
        img_temp.save(buffer, "PNG")

        content = buffer.getvalue()

        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)
        document = response.full_text_annotation

        if document.text == '':
            break
        else:
            text = document.text.replace(' ', '\n')
            raw_table = text.split()
            raw_table.pop(9)
            raw_table.pop(8)
            raw_table.pop(4) 
            table_data.append(dict(zip(table_labels, raw_table)))

            index += 45

    print(f'table_data: {table_data}')

    data = {
        'npi': npi_number,
        'plan': plan_name,
        'product': product_name,
        'client': {
            'id': client_id,
            'name': client_name
        },
        'subclient': {
            'id': subclient_id,
            'name': subclient_name
        },
        'network': network,
        'table': table_data
    }

    json_string = json.dumps(data)
    with open(JSON_PATH, 'w') as outfile:
        outfile.write(json_string)


if __name__ == "__main__":
    main()