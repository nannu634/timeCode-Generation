from docx import Document

def convert_docx_to_lab(input_file_path, output_file_path):
    try:
        doc = Document(input_file_path)
        
        with open(output_file_path, 'w', encoding='utf-8') as lab_file:
            for paragraph in doc.paragraphs:
                lab_file.write(f"<s> {paragraph.text} </s>\n")

        print("Conversion successful.")
    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"Error during file conversion: {str(e)}")