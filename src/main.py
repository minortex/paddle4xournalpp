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

def process_pdf(engine, file_path, output_path, dpi=288):
    """Processes a PDF file, performs OCR, and saves with embedded text."""
    doc = fitz.open(file_path)
    
    print(f"\n--- OCR Results for {os.path.basename(file_path)} (DPI: {dpi}) ---")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        inv_matrix = ~matrix
        pix = page.get_pixmap(dpi=dpi)
        img_path = f"temp_page_{page_num}.png"
        pix.save(img_path)

        try:
            result = engine(img_path)
            if result:
                # result.vis(f"vis_result_page_{page_num}.jpg")
                
                print(f"\nPage {page_num + 1}:")
                if result.txts:
                    for i in range(len(result.txts)):
                        text = result.txts[i]
                        score = result.scores[i]
                        img_box = result.boxes[i]

                        pdf_box = []
                        for point in img_box:
                            pdf_point = fitz.Point(point) * inv_matrix
                            pdf_box.append((pdf_point.x, pdf_point.y))

                        print(f"  Text: {text}")
                        print(f"  Image Box: {img_box.tolist()}")
                        print(f"  PDF Box: {pdf_box}")
                        print(f"  Score: {score:.4f}")

                        # Manually calculate fontsize based on box height
                        rect = fitz.Rect(pdf_box[0], pdf_box[2])
                        font_size = round(rect.height * 0.8) # Use 80% of box height, should be fine with insert_text
                        if font_size < 4: font_size = 4 # Set a minimum font size

                        # --- Manual Justification Logic ---
                        # Calculate the original width of the text
                        original_width = fitz.get_text_length(text, fontname="china-ss", fontsize=font_size)
                        
                        # Target width is the width of the bounding box
                        target_width = rect.width

                        # Avoid division by zero and only scale if text is smaller than the box
                        if original_width > 0 and target_width > original_width:
                            # Create a scaling matrix to stretch the text horizontally
                            scale_matrix = fitz.Matrix(target_width / original_width, 1)
                            # Use insert_text with morphing to stretch the text
                            page.insert_text(rect.bl, text, fontname="china-ss", fontsize=font_size, render_mode=3, morph=(rect.bl, scale_matrix))
                        else:
                            # If text is already wider, or something is wrong, insert normally without stretching
                            page.insert_text(rect.bl, text, fontname="china-ss", fontsize=font_size, render_mode=3)
                else:
                    print("  No text recognized on this page.")
        finally:
            os.remove(img_path)
            
    print(f"\nSaving output to {output_path}...")
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print("Output PDF saved successfully.")            
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

    # if result:
        # result.vis("vis_result.jpg")

def main():
    """Main function to handle command-line arguments and orchestrate OCR processing."""
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_path> <output_path> [--dpi <value>]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    dpi = 288  # Default DPI

    # Basic argument parsing for --dpi
    if '--dpi' in sys.argv:
        try:
            dpi_index = sys.argv.index('--dpi') + 1
            if dpi_index < len(sys.argv):
                dpi = int(sys.argv[dpi_index])
            else:
                print("Error: --dpi flag requires a value.")
                sys.exit(1)
        except (ValueError, IndexError):
            print("Error: Invalid DPI value.")
            sys.exit(1)
    
    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        sys.exit(1)

    engine = initialize_ocr_engine()
    
    file_ext = os.path.splitext(input_path)[-1].lower()
    if file_ext == '.pdf':
        process_pdf(engine, input_path, output_path, dpi)
    else:
        # For simplicity, image processing won't save a new file in this example
        print("Processing single image (output will not be saved to a new file).")
        process_image(engine, input_path)

if __name__ == "__main__":
    main()
