import math
from PIL import Image
import io
import json
import uuid

from google.cloud import vision

def main(filename=None):
    if (filename != None):
        IMAGE_PATH = filename
    else:
        IMAGE_PATH = 'dataset/center.jpg'

    client = vision.ImageAnnotatorClient()

    img = Image.open(IMAGE_PATH)
    
    # get doc text
    # img_temp = img.copy()
    # buffer = io.BytesIO()
    # img_temp.save(buffer, "PNG")

    # content = buffer.getvalue()
    # image = vision.Image(content=content)

    # response = client.text_detection(image=image)
    text = "Explanation of Benefits\n(THIS IS NOT A BILL)\nDELTA DENTAL\nPatient Name\nBusiness/Dentist: CORNERSTONE DENTAL PLLC\nDate of Birth:\nLicense No.:\n5865 / OK (NPI: 1992928196)\nRelationship:\nCheck No.:\nSubscriber:\nIssue Date:\n12/10/2021\nReceipt Date:\n12/08/2021\nSubscriber ID:\nClaim No.:\nPatient Acct:\nPay To: C= Custodial Parent\nS= Subscriber\nP= Provider\nA= Alternate Provider\nArea/Tooth\nCode/Surface\nDate of\nProcedure\nSubmitted\nMaximum\nContract Dentist!\nAdjustment\nAllowed\nAmount\nDeductible / Patient\nCo-Pay / Office Visits\nPatient\nPay\nTo\nService\nCode\nAmount\nApproved Fee\nCo-Pay %\nPayment\nPayment\nPLAN: DELTA DENTAL PLAN OF MICHIGAN\nPRODUCT: DELTA DENTAL PPO (POINT-OF-SERVICE)\nCLIENT/ID: 1166\nSUBCLIENT : 5000\nUAW RETIREE MEDICAL BENEFITS TRUST\nGENERAL MOTORS UAW RETIREES\nNETWORK: PPO DENTIST\n12/07/21\n12/07/21\nD0140\n72.00\n44.00\n28.00\n44.00\n100%\n44.00\n0.00\nD0220\n30.00\n18.00\n12.00\n18.00\n100%\n18.00\n0.00\n102.00\n62.00\n40.00\n62.00\n0.00\n62.00\nTotal\n0.00\nGENERAL MAXIMUM USED TO DATE:\n227.00\nDELTA DENTAL\nA DELTA DENTAL\nPO BOX 9085\nFARMINGTON HILLS, MI 48333-9085\nwww.deltadentalmi.com\nPayment for these services is determined in\naccordance with the specific terms of the\nmember's dental plan and/or Delta Dental's\nagreements with its contracting dentists.\nFOR INQUIRIES: 800-524-0149\n000000001101\nANTI-FRAUD TOLL FREE NUMBER 800-524-0147\nInsurance fraud significantly increases the cost\nof health care. If you are aware of any false\ninformation submitted to Delta Dental, you can\nhelp us lower these costs by calling our toll-free\nhotline. You do not need to identify yourself. Only\nANTI-FRAUD calls can be accepted on this line.\nCORNERSTONE DENTAL PLLC\n1601 AIRPORT DR\nSHAWNEE, OK 74804-4302\nDentist Copy\nPage 1 of 1\n09-25-2019\n**.** :\n"

    npi_start = text.find('NPI: ')+5
    npi_end = text.find(')', npi_start)
    npi_number = text[npi_start:npi_end]

    print(npi_number)

    plan_start = text.find('PLAN: ')+6
    plan_end = text.find('\n', plan_start)
    plan = text[plan_start:plan_end]

    print(plan)

    product_start = text.find('PRODUCT: ')+9
    product_end = text.find('\n', product_start)
    product = text[product_start:product_end]
    print(product)

    client_start = text.find('CLIENT/ID: ')+11
    client_end = text.find('\n', client_start)
    client_id = text[client_start:client_end]

    print(client_id)

    subclient_start = text.find('SUBCLIENT: ')+11
    subclient_end = text.find('\n', subclient_start)
    subclient_id = text[subclient_start:subclient_end]
    print(subclient_id)

    client_startn = subclient_end+1
    client_endn = text.find('\n', client_startn)
    client_name = text[client_startn:client_endn]
    print(client_name)

    subclient_startn = client_endn+1
    subclient_endn = text.find('\n', subclient_startn)
    subclient_name = text[subclient_startn:subclient_endn]
    print(subclient_name)

if __name__ == "__main__":
    main()