#!/usr/bin/env python3
import sys
import os
from PIL import Image
import numpy as np
import math
from ISR.models import RDN
import io
import struct

DEBUG = os.getenv('DEBUG')
if DEBUG == '0' or DEBUG is None:
    DEBUG = False


def PSNR(img1, img2):
    mse = np.mean((img1-img2)**2)
    if mse == 0:
        return 100
    PIXEL_MAX = 255.0
    return 20*math.log10(PIXEL_MAX/math.sqrt(mse))


def SR(lr_img: np.array) -> np.array:
    # rdn = RDN(arch_params=dict(C=6, D=20, G=64, G0=64, x=2))
    # rdn.model.load_weights(
    #     '/home/sudongpo/Downloads/image-super-resolution/weights/sample_weights/rdn-C6-D20-G64-G064-x2/PSNR-driven/rdn-C6-D20-G64-G064-x2_PSNR_epoch086.hdf5')
    rdn = RDN(arch_params=dict(C=3, D=10, G=64, G0=64, x=2))
    weights_file = os.path.join(
        os.path.split(sys.argv[0])[0],
        'PSNR-driven/rdn-C3-D10-G64-G064-x2_PSNR_epoch134.hdf5'
    )
    rdn.model.load_weights(weights_file)
    sr_img = rdn.predict(lr_img)
    return sr_img


def getFileName(fn):
    if not os.path.exists(fn):
        return fn
    fname, fext = os.path.splitext(fn)
    num = 1
    while os.path.exists(fname+'('+str(num)+')'+fext):
        num += 1
    return fname+'('+str(num)+')'+fext


def compress(infile, outfile):
    print(f"Compressing {infile}...")
    try:
        in_img = Image.open(infile)
    except IOError as err:
        print("IO Error: {}".format(err))
        raise

    thumbnail_size = (in_img.width//2, in_img.height//2)
    thumbnail = in_img.copy()
    thumbnail.thumbnail(thumbnail_size)

    if DEBUG:
        thumbnail.save(getFileName('output1.jpg'))

    thumbnail_output = io.BytesIO()
    thumbnail.save(thumbnail_output, format='jpeg')

    thumbnail = Image.open(thumbnail_output)
    thumbnail_arr = np.array(thumbnail)
    thumbnail_sr_arr = SR(thumbnail_arr)

    if DEBUG:
        print(
            f'(in_img.height, in_img.width) = f{(in_img.height, in_img.width)}'
        )
        print(f'thumbnail_sr_arr.shape = f{thumbnail_sr_arr.shape}')
    if thumbnail_sr_arr.shape[:2] != (in_img.height, in_img.width):
        DEBUG and print(f'resizing thumbnail_sr...')
        thumbnail_sr_arr = np.array(
            Image.fromarray(thumbnail_sr_arr).resize(
                (in_img.width, in_img.height))
        )

    if DEBUG:
        thumbnail_sr = Image.fromarray(thumbnail_sr_arr)
        thumbnail_sr.save(getFileName('sr.png'))

    delta = Image.fromarray(np.array(in_img) ^ thumbnail_sr_arr)
    # delta.save('output2.jpg', quality=95, optimize=True)
    delta_output = io.BytesIO()
    delta.save(delta_output, format='png')

    if DEBUG:
        delta.save(getFileName('output2.png'))

    # create outputs
    thumbnail_output = thumbnail_output.getvalue()
    delta_output = delta_output.getvalue()
    thumbnail_output_size = len(thumbnail_output)
    thumbnail_output_size_output = struct.pack('<I', thumbnail_output_size)

    # write to file
    try:
        of_img = open(outfile, 'wb')
    except OSError as err:
        print("OS error: {}".format(err))
        raise
    else:
        of_img.write(thumbnail_output_size_output)
        of_img.write(thumbnail_output)
        of_img.write(delta_output)
        of_img.close()


def srp2PILImage(infile):
    try:
        if_img = open(infile, 'rb')
    except OSError as err:
        print("OS error: {}".format(err))
        raise
        return

    data = if_img.read()

    thumbnail_size = struct.unpack('<I', data[0:4])[0]
    thumbnail_data = data[4:4+thumbnail_size]
    delta_data = data[4+thumbnail_size:]

    thumbnail_data = io.BytesIO(thumbnail_data)
    delta_data = io.BytesIO(delta_data)

    thumbnail_sr_arr = SR(np.array(Image.open(thumbnail_data)))
    delta_arr = np.array(Image.open(delta_data))
    if thumbnail_sr_arr.shape != delta_arr.shape:
        thumbnail_sr_arr = np.array(
            Image.fromarray(thumbnail_sr_arr).resize(
                tuple(reversed(delta_arr.shape[:2]))
            )
        )

    origin = Image.fromarray(thumbnail_sr_arr ^ delta_arr)
    return origin


def decompress(infile, outfile):
    print(f"Decompressing {infile}...")
    origin = srp2PILImage(infile)
    origin.save(outfile)
    origin.close()


def show(srp):
    origin = srp2PILImage(srp)
    origin.show()


def main():
    if len(sys.argv) == 1:
        # interact with user
        pass
    else:
        # CLI
        for infile in sys.argv[1:]:
            fname, fext = os.path.splitext(infile)
            if fext == '.srp':
                # decompress(infile, fname+'.png')
                show(infile)
            else:
                compress(infile, fname+'.srp')
        print("done")


if __name__ == '__main__':
    main()
