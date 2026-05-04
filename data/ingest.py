import pdfplumber
import os

DATA_DIR = os.path.abspath(os.path.dirname(__file__))

def extract_text(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

if __name__ == "__main__":
    pdf_file = os.path.join(DATA_DIR, "sp21.pdf")
    if os.path.exists(pdf_file):
        text = extract_text(pdf_file)
        if text:
            out_file = os.path.join(DATA_DIR, "raw.txt")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text)
            print("Ingestion complete.")
        else:
            print("No text extracted.")
    else:
        print(f"PDF file not found at {pdf_file}.")