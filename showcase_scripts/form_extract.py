import csv
import io
import math
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

from google.cloud import vision
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from showcase_scripts.search import find_word_location, find_words_location

_DEFAULT_POOL = ThreadPoolExecutor()

def threadpool(f, executor=None):
    @wraps(f)
    def wrap(*args, **kwargs):
        return (executor or _DEFAULT_POOL).submit(f, *args, **kwargs)

    return wrap


OUT_DIR = 'output'


def fix_skew(img, client):
    width, height = img.size

    PLAN_H = 0.294242424242*height

    # fix tilt
    img_temp = img.copy()
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    document = response.full_text_annotation
    page = document.pages[0]

    vertices = page.blocks[0].bounding_box.vertices
    tilt_angle = math.atan2(vertices[3].y-vertices[2].y,vertices[2].x-vertices[3].x) * (180/math.pi)
    img = img.rotate(-tilt_angle)

    # fix translate 
    location_dentist = find_words_location(document, 'Explanation of Benefits')

    dentist_midpointw = (location_dentist.vertices[2].x + location_dentist.vertices[3].x)/2
    doc_midpointw = width/2
    translatew = doc_midpointw - dentist_midpointw

    location_plan = find_word_location(document, 'PLAN:')
    plan_midpointh = (location_plan.vertices[0].y + location_plan.vertices[3].y)/2
    translateh = PLAN_H - plan_midpointh

    transform_mat = (1, 0, -translatew, 0, 1, -translateh)
    img = img.transform(size=(width, height), method=Image.Transform.AFFINE, data=transform_mat)

    return img


@threadpool
def get_npi(img, client):
    width, height = img.size

    # image for NPI
    img_temp = img.crop((width/1.45, height/8, width, height/6))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content = content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    npi_idx = document.text.find('NPI: ')
    if (npi_idx == -1):
        npi_idx = document.text.find('NPI; ')
    provider = document.text[npi_idx+5:document.text.find(')')].strip()
    print(f'provider: {provider}')

    return provider


@threadpool
def get_header(img, client):
    width, height = img.size

    # image for header
    img_temp = img.crop((0, height/4, width, height/2.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    text = document.text.split('PRODUCT:')[1]
    product = text.strip()
    product = product[:product.find('\n')]
    print(f'product: {product}')

    text = document.text.split('PLAN: ')[1]
    insurance = text[:text.find('\n')]
    print(f'insurance: {insurance}')

    text = document.text.split('CLIENT/ID: ')[1]
    group_p1 = text[:text.find(' ')]
    text = text[len(group_p1)+1:]

    group_name = text[:text.find('\n')]
    group_name = group_name.replace(']','J').replace(')','J').strip()
    print(f'group_name: {group_name}')

    text = document.text.split('SUBCLIENT: ')[1]
    group_p2 = text[:text.find(' ')]

    group_id = '-'.join([group_p1, group_p2])
    print(f'group_id: {group_id}')

    text = text.split('NETWORK: ')[1]

    network = text[:text.find('\n')]
    print(f'network: {network}')

    network = 'Yes' if network == 'PPO DENTIST' or network == 'PREMIER DENTIST' else 'No'

    return (product, insurance, group_name, group_id, network)


@threadpool
def get_table1(img, client):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/8, height/2.9, width/2, height/1.7))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    # fix me
    num_entries = 0
    entry_idx = 2
    while not table_string[0].isnumeric():
        table_string = table_string[1:]

    while (table_string[entry_idx] == '/'):
        num_entries += 1
        entry_idx += 9

    table_data = []
    for i in range(num_entries):
        table_data.append({})

    # add dates
    for i in range(num_entries):
        date = table_string[:table_string.find('\n')]
        table_string = table_string[len(date)+1:]
        table_data[i]['date'] = date

    # add codes
    for i in range(num_entries):
        procedure_code = table_string[:table_string.find('\n')]
        if (procedure_code[0] == '0'):
            procedure_code = 'D' + procedure_code[1:]
        table_string = table_string[len(procedure_code)+1:]
        table_data[i]['procedure_code'] = procedure_code
    
    # add submitted amount
    for i in range(num_entries):
        submitted_amount = table_string[:table_string.find('\n')]
        table_string = table_string[len(submitted_amount)+1:]
        table_data[i]['submitted_amount'] = submitted_amount

    # maximum approved fee
    for i in range(num_entries):
        max_approved = table_string[:table_string.find('\n')]
        table_string = table_string[len(max_approved)+1:]
        table_data[i]['max_approved'] = max_approved

    # contract dentist adjustment
    for i in range(num_entries):
        contract_adj = table_string[:table_string.find('\n')]
        table_string = table_string[len(contract_adj)+1:]
        table_data[i]['contract_adj'] = contract_adj
    
    return table_data


@threadpool
def get_table2(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/2, height/2.9, width, height/1.7))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()
    table_data = res_table.result()

    num_entries = len(table_data)

    # deductible
    for i in range(num_entries):
        if table_string[0] == 'D':
            deduct = table_string[:table_string.find('\n')]
            table_string = table_string[len(deduct)+1:]
        elif table_string[0] == '0':
            deduct = table_string[:table_string.find('\n')]
            deduct = 'D' + deduct[1:]
            table_string = table_string[len(deduct)+1:]
        else:
            deduct = '-'
        table_data[i]['deduct'] = deduct

    #patient co-pay
    for i in range(num_entries):
        if table_string[0] == 'P':
            patient_copay = table_string[:table_string.find('\n')]
            table_string = table_string[len(patient_copay)+1:]
        else:
            patient_copay = '-'
        table_data[i]['patient_copay'] = patient_copay

    # allowed amount
    for i in range(num_entries):
        allowed_amount = table_string[:table_string.find('\n')]
        table_string = table_string[len(allowed_amount)+1:]
        table_data[i]['allowed_amount'] = allowed_amount

    # co-pay
    for i in range(num_entries):
        co_pay = table_string[:table_string.find('\n')]
        table_string = table_string[len(co_pay)+1:]
        table_data[i]['co_pay'] = co_pay
    
    # payment
    for i in range(num_entries):
        payment = table_string[:table_string.find('\n')]
        table_string = table_string[len(payment)+1:]
        table_data[i]['payment'] = payment
    
    # patient payment
    for i in range(num_entries):
        patient_payment = table_string[:table_string.find('\n')]
        table_string = table_string[len(patient_payment)+1:]
        if patient_payment[-1].isalpha():
            patient_payment = patient_payment[:-1]
        table_data[i]['patient_payment'] = patient_payment

    print(f'table_data: {table_data}')

    return table_data



def extract(filename=None):
    if (filename != None):
        IMAGE_PATH = filename
    else:
        IMAGE_PATH = 'dataset/eob2.jpg'

    client = vision.ImageAnnotatorClient()

    # img = process_image_for_ocr(IMAGE_PATH)

    img = Image.open(IMAGE_PATH)
    width, height = img.size

    img = fix_skew(img, client)

    # provider = get_npi(img, client)
    res_npi = get_npi(img, client)

    # product, insurance, group_name, group_id, network = get_header(img, client)
    res_header = get_header(img, client)

    # table_data = get_table(img, client)
    res_table = get_table1(img, client)

    res_table = get_table2(img, client, res_table)

    csv_header = ['Insurance','CONTRACT ACCESS','Network','Provider','Group','Group ID','Date of Service','Submitted Code','Approved Code','Submitted Amount','Approved Amount', 'Allowed Amount','Deductible','Co-Pay','Other Insurance','Co-Pay (%)','Payment','Max Met']
    form_id = str(uuid.uuid4())
    with open(os.path.join(OUT_DIR, form_id+'.csv'), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(csv_header)
        provider = res_npi.result()
        (product, insurance, group_name, group_id, network) = res_header.result()
        rows = []
        for item in res_table.result():

            if float(item['max_approved']) != float(item['submitted_amount']) - float(item['contract_adj']):
                print('something wrong with doc parsing')
                break

            rows.append([insurance,
                        product,
                        network, 
                        provider, 
                        group_name, 
                        group_id, 
                        item['date'], 
                        item['procedure_code'], 
                        item['procedure_code'], 
                        item['submitted_amount'], 
                        item['max_approved'], 
                        item['allowed_amount'],
                        item['deduct'],item['patient_copay'],'-',
                        item['co_pay'],
                        item['payment'],''])

        writer.writerows(rows)

    img.close()

    return rows, form_id


if __name__ == "__main__":
    extract()
