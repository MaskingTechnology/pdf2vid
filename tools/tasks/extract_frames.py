
from pdf2image import convert_from_path

RESOLUTION = 200

def extract_frames(pdf_file, output_folder, page_numbers = None):

    images = convert_from_path(pdf_file, dpi=RESOLUTION, thread_count=4)

    for index, image in enumerate(images):
        
        image.save(f"{output_folder}/{index + 1:03}.png", "PNG")
