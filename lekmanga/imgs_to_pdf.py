import os
import sys
from PIL import Image

def images_to_pdf(all_image_paths, output_pdf_path):
    images = []
    for img_path in all_image_paths:
        img = Image.open(img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)

    if images:
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        print(f" Saved PDF at: {output_pdf_path}")
    else:
        print(" No images found to convert.")

def collect_all_images(manga_folder):
    all_images = []
    for chapter in sorted(os.listdir(manga_folder)):
        chapter_path = os.path.join(manga_folder, chapter)
        if os.path.isdir(chapter_path):
            image_files = [os.path.join(chapter_path, f) for f in sorted(os.listdir(chapter_path)) if f.lower().endswith(('jpg', 'jpeg', 'png'))]
            all_images.extend(image_files)
    return all_images

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_manga.py ./relative/path/to/manga_folder")
        sys.exit(1)

    manga_folder = os.path.abspath(sys.argv[1])

    if not os.path.isdir(manga_folder):
        print(f" Error: '{manga_folder}' is not a valid folder.")
        sys.exit(1)

    all_image_paths = collect_all_images(manga_folder)
    output_pdf_path = os.path.join(manga_folder, "manga.pdf")
    images_to_pdf(all_image_paths, output_pdf_path)
