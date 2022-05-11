import csv
import io
import math
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

from google.cloud import vision
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from showcase_scripts.search import find_word_location, find_words_location

_DEFAULT_POOL = ThreadPoolExecutor()

def threadpool(f, executor=None):
    @wraps(f)
    def wrap(*args, **kwargs):
        return (executor or _DEFAULT_POOL).submit(f, *args, **kwargs)

    return wrap


OUT_DIR = 'static'


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

    vertices = page.blocks[1].bounding_box.vertices
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

    img_temp.close()

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

    img_temp.close()

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
    
    img_temp.close()

    return (product, insurance, group_name, group_id, network)

@threadpool
def get_dates(img, client):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/6.9, height/2.9, width/4.64, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    num_entries = len(document.pages[0].blocks[0].paragraphs[0].words)

    table_data = []
    for i in range(num_entries):
        table_data.append({})

    for i in range(num_entries):
        date = table_string[:table_string.find('\n')]
        table_string = table_string[len(date)+1:]
        table_data[i]['date'] = date

    img_temp.close()

    return table_data

@threadpool
def procedure_codes(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/4.5, height/2.9, width/3.65, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # add codes
    for i in range(num_entries):
        procedure_code = table_string[:table_string.find('\n')]
        if (procedure_code[0] == '0'):
            procedure_code = 'D' + procedure_code[1:]
        table_string = table_string[len(procedure_code)+1:]
        table_data[i]['procedure_code'] = procedure_code

    img_temp.close()
    
    return table_data

@threadpool
def submitted_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/3.5, height/2.9, width/2.8, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # add submitted amount
    for i in range(num_entries):
        submitted_amount = table_string[:table_string.find('\n')]
        table_string = table_string[len(submitted_amount)+1:]
        table_data[i]['submitted_amount'] = submitted_amount

    img_temp.close()
    
    return table_data

@threadpool
def approved_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/2.7, height/2.9, width/2.245, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # maximum approved fee
    for i in range(num_entries):
        max_approved = table_string[:table_string.find('\n')]
        table_string = table_string[len(max_approved)+1:]
        table_data[i]['max_approved'] = max_approved

    img_temp.close()

    return table_data

@threadpool
def adjust_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/2.6 + 180, height/2.9, width/2.245 + 154, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # contract dentist adjustment
    for i in range(num_entries):
        contract_adj = table_string[:table_string.find('\n')]
        table_string = table_string[len(contract_adj)+1:]
        table_data[i]['contract_adj'] = contract_adj

    img_temp.close()
    
    return table_data

@threadpool
def allowed_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((width/1.9, height/2.9, width/1.718, height/1.9))
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
        # if table_string[0] == 'D':
        #     deduct = table_string[:table_string.find('\n')]
        #     table_string = table_string[len(deduct)+1:]
        # else:
        deduct = '-'
        table_data[i]['deduct'] = deduct

    #patient co-pay
    for i in range(num_entries):
        # if table_string[0] == 'P':
        #     patient_copay = table_string[:table_string.find('\n')]
        #     table_string = table_string[len(patient_copay)+1:]
        # else:
        patient_copay = '-'
        table_data[i]['patient_copay'] = patient_copay

    # allowed amount
    for i in range(num_entries):
        allowed_amount = table_string[:table_string.find('\n')]
        table_string = table_string[len(allowed_amount)+1:]
        table_data[i]['allowed_amount'] = allowed_amount

    img_temp.close()
    
    return table_data

@threadpool
def copay_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((1764, height/2.9, 1875, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # co-pay
    for i in range(num_entries):
        co_pay = table_string[:table_string.find('\n')]
        table_string = table_string[len(co_pay)+1:]
        table_data[i]['co_pay'] = co_pay

    img_temp.close()

    return table_data

@threadpool
def payment_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((1885, height/2.9, 2075, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # payment
    for i in range(num_entries):
        payment = table_string[:table_string.find('\n')]
        table_string = table_string[len(payment)+1:]
        table_data[i]['payment'] = payment

    img_temp.close()

    return table_data

@threadpool
def patient_amounts(img, client, res_table):
    width, height = img.size

    # image of form table
    img_temp = img.crop((2090, height/2.9, 2290, height/1.9))
    buffer = io.BytesIO()
    img_temp.save(buffer, "PNG")

    content = buffer.getvalue()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    table_string = document.text.upper()

    table_data = res_table.result()
    num_entries = len(table_data)

    # patient payment
    for i in range(num_entries):
        patient_payment = table_string[:table_string.find('\n')]
        table_string = table_string[len(patient_payment)+1:]
        if patient_payment[-1].isalpha():
            patient_payment = patient_payment[:-1]
        table_data[i]['patient_payment'] = patient_payment

    print(f'table_data: {table_data}')

    img_temp.close()
    
    return table_data

def extract(filename=None):
    if (filename == None):
        IMAGE_PATH = 'eob10.jpg'
    else:
        IMAGE_PATH = filename
        

    client = vision.ImageAnnotatorClient()

    # img = process_image_for_ocr(IMAGE_PATH)

    img = Image.open('static/' + IMAGE_PATH)

    img = fix_skew(img, client)

    res_npi = get_npi(img, client)

    res_header = get_header(img, client)

    res_table = get_dates(img, client)

    res_table = procedure_codes(img, client, res_table)

    res_table = submitted_amounts(img, client, res_table)
    
    res_table = approved_amounts(img, client, res_table)

    # no need to run this
    # res_table = adjust_amounts(img, client, res_table)

    res_table = allowed_amounts(img, client, res_table)

    res_table = copay_amounts(img, client, res_table)
    
    res_table = payment_amounts(img, client, res_table)

    res_table = patient_amounts(img, client, res_table)

    csv_header = ['Insurance','CONTRACT ACCESS','Network','Provider','Group','Group ID','Date of Service','Submitted Code','Approved Code','Submitted Amount','Approved Amount', 'Allowed Amount','Deductible','Co-Pay','Other Insurance','Co-Pay (%)','Payment','Max Met']

    provider = res_npi.result()
    (product, insurance, group_name, group_id, network) = res_header.result()

    rows = []
    for item in res_table.result():
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

    form_id = IMAGE_PATH[:-4]
    if filename == None:
        with open(os.path.join(OUT_DIR, form_id+'.csv'), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(csv_header)
            writer.writerows(rows)
    img.close()

    return rows, form_id


if __name__ == "__main__":
    extract()
