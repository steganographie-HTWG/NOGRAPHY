import json
from embedder import embedder
from encoder import encoder
import os
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO
import string


def lambda_handler(event, context):
    placeholder = "In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends of worms and an oozy smell, nor yet a dry, bare, sandy hole with nothing in it to sit down on or to eat: it was a hobbit-hole, and that means comfort."
    secret = "LOTR is better than GOT"
    encoded_secret = [int(c, 2) for c in encoder.encode(secret)]

    image = Image.new("RGB", (500, 200), 'white')

    letters_and_fonts = get_letters_and_fonts(placeholder, secret)

    fit_text(image, letters_and_fonts, (0, 0, 0), 50)

    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image_str = base64.b64encode(buffered.getvalue())
    return {
        "statusCode": 200,
        "headers": {
            'Content-Type': 'image/png'
        },
        "body": image_str,
        "isBase64Encoded": True
    }

    #placeholder = event['placeholder'].strip()
    #show_colors = event['show_colors']

    # if len(secret) * ENCODING_DECODING_BASE > len(placeholder):
    #    return {
    #        "statusCode": 400,
    #        "error": "Secret is too long. Make it shorter or the placeholder longer."
    #    }
    # else:

    # encoded_secret = encoder.encode(secret, ENCODING_DECODING_BASE)
    # document = embedder.embed(
    #                 embedder.setup_document(),
    #                 placeholder,
    #                 encoded_secret,
    #                 show_colors
    #             )


def get_letters_and_fonts(placeholder, encoded_secret):
    letters_and_fonts = []
    index = 0
    while index < len(placeholder):
        if placeholder[index] in string.ascii_letters:
            if index < len(encoded_secret):
                letters_and_fonts.append(
                    (placeholder[index], encoded_secret[index]))
            else:
                letters_and_fonts.append((placeholder[index], 0))
            index = index + 1
        else:
            letters_and_fonts.append((placeholder[index], 0))
            # slicing out the non-ASCII character, so it won't block the index
            placeholder = placeholder[:index] + placeholder[index+1:]
    return letters_and_fonts


# based on https://stackoverflow.com/questions/58041361/break-long-drawn-text-to-multiple-lines-with-pillow
def break_fix(text, width, font, draw):
    if not text:
        return
    lo = 0
    hi = len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        t = text[:mid]
        w, h = draw.textsize(t, font=font)
        if w <= width:
            lo = mid
        else:
            hi = mid - 1
    t = text[:lo]
    w, h = draw.textsize(t, font=font)
    yield t, w, h
    yield from break_fix(text[lo:], width, font, draw)


def fit_text(img, letters_and_fonts, color, margin):
    width = img.size[0] - 2 - margin
    draw = ImageDraw.Draw(img)
    letters = ''.join([i[0] for i in letters_and_fonts])
    measure_font = ImageFont.truetype('./assets/3.ttf', 18)
    pieces = list(break_fix(letters, width, measure_font, draw))
    height = sum(p[2] for p in pieces)
    if height > img.size[1]:
        raise ValueError("text doesn't fit")
    y = (img.size[1] - height) // 2
    for t, w, h in pieces:
        x = (img.size[0] - w) // 2
        # draw each letter with a specific font
        draw.text((x, y), t, font=measure_font, fill=color)
        y += h