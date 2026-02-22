from PIL import Image


def create_pdfs_from_jpgs(input_dict):
    for pdf_filename, jpg_list in input_dict.items():
        # Ensure there are images to process
        if not jpg_list:
            print(f"No images provided for {pdf_filename}. Skipping.")
            continue

        images = []
        for file in jpg_list:
            try:
                img = Image.open(file)
                # Convert images to RGB to ensure compatibility
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)
            except IOError as e:
                print(f"Error opening image file {file}. Skipping this file: {e}")
                continue

        # Save images to PDF if any images were successfully opened
        if images:
            try:
                images[0].save(pdf_filename, save_all=True, append_images=images[1:])
                print(f"Successfully created {pdf_filename}.")
            except Exception as e:
                print(f"Error saving {pdf_filename}: {e}")
        else:
            print(f"No valid images to save for {pdf_filename}. Skipping.")


# Example usage:
input_dict = {
    "filename1.pdf": [
        r"/mnt/d/Scans/1.jpg",
        r"/mnt/d/Scans/2.jpg",
    ],
    "filename2.pdf": [
        r"/mnt/d/Scans/3.jpg",
    ],
}

create_pdfs_from_jpgs(input_dict)
