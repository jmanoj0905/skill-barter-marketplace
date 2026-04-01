from PIL import Image
import io


def generate_thumbnail(image_bytes):

    image = Image.open(io.BytesIO(image_bytes))

    image.thumbnail((200, 200))

    buffer = io.BytesIO()

    image.save(buffer, format="JPEG")

    buffer.seek(0)

    return buffer