import fitz
import os

def extract_text_from_pdf(pdf_file):
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    text = ""
    for page in doc:
        text += page.get_text()

    return text


def extract_images_from_pdf(pdf_file, prefix):
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    os.makedirs("images", exist_ok=True)
    image_paths = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)

            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            path = f"images/{prefix}_p{page_index+1}_{img_index+1}.{image_ext}"

            with open(path, "wb") as f:
                f.write(image_bytes)

            image_paths.append((page_index + 1, path))

    return image_paths