import io
import os

from google.cloud import vision

IMAGE_PATH = 'dataset/original2.jpg'
CLIENT_OPTIONS = {'api_endpoint': 'us-vision.googleapis.com'}

client = vision.ImageAnnotatorClient(
    client_options=CLIENT_OPTIONS
)

with io.open(IMAGE_PATH, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

response = client.document_text_detection(image=image)

for text in response.text_annotations:
    print(f'\n"{text.description}"')

if response.error.message:
    raise Exception(response.error.message)