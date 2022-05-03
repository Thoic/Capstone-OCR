from gettext import find
from enum import Enum
import math
from PIL import Image, ImageDraw
import io

from google.cloud import vision

IMAGE_PATH = 'dataset/center'
IMAGE_PATH2 = 'dataset/original2'


def main():
    client = vision.ImageAnnotatorClient()

    img = Image.open(IMAGE_PATH + '.jpg')

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
    height_adj = math.tan(tilt_angle*(math.pi/180))*width/math.pi


    # fix tilt second
    img_second = Image.open(IMAGE_PATH2 + '.jpg')
    img_second0 = img_second.copy()
    buffer_second = io.BytesIO()
    img_second0.save(buffer_second, "PNG")

    content_second = buffer_second.getvalue()
    image_second = vision.Image(content=content_second)

    response_second = client.text_detection(image=image_second)
    text_second = response_second.full_text_annotation
    page_second = text_second.pages[0]

    vertices_second = page_second.blocks[1].bounding_box.vertices
    tilt_angle_second = math.atan2(vertices_second[3].y-vertices_second[2].y,vertices_second[2].x-vertices_second[3].x) * (180/math.pi)
    img_second = img_second.rotate(-tilt_angle_second)

    width_second, height_second = img_second.size
    height_second_adj = math.tan(tilt_angle_second*(math.pi/180))*width_second/math.pi

    # image with NPI
    img1 = img.crop((width/1.8, height/8 + height_adj, width, height/5 + height_adj))
    buffer1 = io.BytesIO()
    img1.save(buffer1, "PNG")
    img1.show()

    img2 = img_second.crop((width_second/1.8, height_second/8 + height_second_adj, width, height_second/5 + height_second_adj))
    buffer2 = io.BytesIO()
    img2.save(buffer2, "PNG")
    img2.show()
    print(f'')


if __name__ == "__main__":
    main()