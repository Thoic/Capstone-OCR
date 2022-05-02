from gettext import find
from enum import Enum
import math
from PIL import Image, ImageDraw
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/original2'


def main():
    client = vision.ImageAnnotatorClient()

    img = Image.open(IMAGE_PATH + '.jpg')

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
    img.save(IMAGE_PATH + '_fixed.jpg')

if __name__ == "__main__":
    main()