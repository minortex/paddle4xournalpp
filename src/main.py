import sys
import os
import fitz  # PyMuPDF
from rapidocr import RapidOCR, EngineType

def initialize_ocr_engine():
    """Initializes and returns the RapidOCR engine."""
    # config_path = "D:/UserData/Desktop/notes-tools/paddle/source/config.yaml"
    return RapidOCR(params={
        "Global.use_det": True,
        "Global.use_cls": False,
        "Global.use_rec": True,
        "Det.engine_type": EngineType.OPENVINO,
        "Rec.engine_type": EngineType.OPENVINO,
        # "EngineConfig.paddle.use_cuda": True,  # 使用PaddlePaddle GPU版推理
    })

def process_pdf(engine, file_path, dpi=288):
    """Processes a PDF file, performing OCR on each page."""
    doc = fitz.open(file_path)
    
    print(f"\n--- OCR Results for {os.path.basename(file_path)} (DPI: {dpi}) ---")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Create the transformation matrix for coordinate conversion
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        inv_matrix = ~matrix

        # Create a pixmap with the specified DPI
        pix = page.get_pixmap(dpi=dpi)

        # Save page as a temporary image to pass to OCR
        img_path = f"temp_page_{page_num}.png"
        pix.save(img_path)

        try:
            result = engine(img_path)
            if result:
                result.vis(f"vis_result_page_{page_num}.jpg")
                
                print(f"\nPage {page_num + 1}:")
                if result.txts: # Check if there are any recognized texts
                    for i in range(len(result.txts)):
                        text = result.txts[i]
                        score = result.scores[i]
                        img_box = result.boxes[i]

                        # Convert image coordinates back to PDF coordinates
                        pdf_box = []
                        for point in img_box:
                            pdf_point = fitz.Point(point) * inv_matrix
                            pdf_box.append((pdf_point.x, pdf_point.y))

                        print(f"  Text: {text}")
                        print(f"  Image Box: {img_box.tolist()}")
                        print(f"  PDF Box: {pdf_box}")
                        print(f"  Score: {score:.4f}")
                else:
                    print("  No text recognized on this page.")
        finally:
            # Ensure the temporary file is removed
            os.remove(img_path)
            
def process_image(engine, file_path):
    """Processes a single image file."""
    result = engine(file_path)
    
    print(f"\n--- OCR Results for {os.path.basename(file_path)} ---")
    if result and result.txts:
        for i in range(len(result.txts)):
            text = result.txts[i]
            box = result.boxes[i].tolist()
            score = result.scores[i]
            print(f"  Text: {text}")
            print(f"  Box: {box}")
            print(f"  Score: {score:.4f}")
    else:
        print("No text recognized.")

    if result:
        result.vis("vis_result.jpg")

def main():
    """Main function to handle command-line arguments and orchestrate OCR processing."""
    if len(sys.argv) <= 1:
        print("Usage: python main.py <file_path> [--dpi <value>]")
        sys.exit(1)

    file_path = None
    dpi = 288  # Default DPI

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--dpi':
            if i + 1 < len(sys.argv):
                try:
                    dpi = int(sys.argv[i+1])
                    i += 1
                except ValueError:
                    print("Error: DPI value must be an integer.")
                    sys.exit(1)
            else:
                print("Error: --dpi flag requires a value.")
                sys.exit(1)
        elif file_path is None:
            file_path = sys.argv[i]
        i += 1
    
    if file_path is None:
        print("Error: No file path provided.")
        sys.exit(1)

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    engine = initialize_ocr_engine()
    
    file_ext = os.path.splitext(file_path)[-1].lower()
    if file_ext == '.pdf':
        process_pdf(engine, file_path, dpi)
    else:
        process_image(engine, file_path)

if __name__ == "__main__":
    main()
