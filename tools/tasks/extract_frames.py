
import glob
import argparse
from wand.image import Image

RESOLUTION = 300
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

def extract_frames(pdf_file, output_folder, page_numbers = None):

    with Image(filename=pdf_file, resolution=RESOLUTION) as pages:

        if page_numbers is None:
            page_numbers = range(len(pages.sequence))
        
        for index in page_numbers:

            with pages.sequence[index].clone() as page:
                
                page.format = 'png'
                page.resize(TARGET_WIDTH, TARGET_HEIGHT)

                file_number = str(index + 1).zfill(3)
                output_file = f"{output_folder}/{file_number}.png"

                page.save(filename=output_file)

                print(f" ► Converted page {index + 1} as {output_file}")
