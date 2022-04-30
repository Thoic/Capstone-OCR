from gettext import find
from enum import Enum
import math
from PIL import Image, ImageDraw
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/center'


def main():
    client = vision.ImageAnnotatorClient()

    img = Image.open(IMAGE_PATH + '.jpg')
    width, height = img.size
    img1 = img.crop((0, 0, width/3, height/8))
    buffer = io.BytesIO()
    img1.save(buffer, "PNG")

    content = buffer.getvalue()
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    vertices = texts[2].bounding_poly.vertices
    tilt_angle = math.atan2(vertices[3].y-vertices[0].y,vertices[0].x-vertices[3].x) * (180/math.pi)
    img = img.rotate(90-tilt_angle)
    img.save(IMAGE_PATH + '_fixed.jpg')

if __name__ == "__main__":
    main()