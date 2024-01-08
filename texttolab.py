def convert_txt_to_lab(input_file_path, output_file_path):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as txt_file:
            lines = txt_file.readlines()

        with open(output_file_path, 'w', encoding='utf-8') as lab_file:
            for line in lines:
                lab_file.write(f"<s> {line.strip()} </s>\n")

        print("Conversion successful.")
    except FileNotFoundError:
        print("File not found. Please check the file path.")
    except Exception as e:
        print(f"Error during file conversion: {str(e)}")
