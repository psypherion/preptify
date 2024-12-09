from pdf2image import convert_from_path
from io import BytesIO
import os
from typing import List

class PDFToImageConverter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_name = pdf_path.split("/")[-1].split(".")[0]
    
    async def convert_pdf_to_images(self) -> List[BytesIO]:
        """
        Converts each page of the PDF to an in-memory image (JPEG format) using pdf2image.
        """
        # Convert PDF to images in memory
        images = convert_from_path(self.pdf_path, dpi=300)
        image_streams = []

        for image in images:
            img_io = BytesIO()
            image.save(img_io, "JPEG")
            img_io.seek(0)  # Reset the file pointer to the start
            image_streams.append(img_io)

        print(f"Converted {len(image_streams)} pages")
        for idx, img in enumerate(image_streams):
            print(f"Page {idx+1} Image Size: {len(img.getvalue())} bytes")  
        
        return image_streams

    async def pdf_length(self) -> int:
        """
        Returns the number of pages in the PDF.
        """
        return len(await self.convert_pdf_to_images())
    
    async def save_images(self, image_streams: List[BytesIO]):
        """
        Save the images to a directory.
        """
        # Define the directory to save images
        save_dir = os.path.join(os.getcwd(), f"{self.pdf_name}/images")
        os.makedirs(save_dir, exist_ok=True)

        for idx, img in enumerate(image_streams):
            image_path = os.path.join(save_dir, f"page_{idx+1}.jpg")
            with open(image_path, "wb") as f:
                f.write(img.getvalue())

        print(f"Saved {len(image_streams)} images to {save_dir}")
        return save_dir


# Convert PDF pages to images

async def main():
    pdf_slicer = PDFToImageConverter(pdf_path=r"pdfs/paper_2_X.pdf")
    image_streams = await pdf_slicer.convert_pdf_to_images()
    await pdf_slicer.save_images(image_streams)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
