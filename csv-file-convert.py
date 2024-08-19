import csv
from korean_roman import HangeulRomaja

def convert_csv(input_file, output_file):
    # CSV 파일을 읽고 로마자로 변환
    with open(input_file, mode='r', encoding='utf-8-sig') as infile, \
         open(output_file, mode='w', newline='', encoding='utf-8-sig') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        romaja_converter = HangeulRomaja()

        for row in reader:
            if len(row) >= 2:  # 최소 두 번째 필드가 있어야 함
                original_text = row[1]  # 두 번째 필드 (한글)
                romanized_text = romaja_converter.convert(original_text, conversion_type=HangeulRomaja.TYPE_DEFAULT)
                if len(row) >= 3:
                    row[2] = romanized_text  # 세 번째 필드에 저장
                else:
                    row.append(romanized_text)  # 세 번째 필드가 없다면 추가
            writer.writerow(row)

if __name__ == "__main__":
    # 입력 파일과 출력 파일 경로를 지정
    input_csv = './정류장영문명.csv'  # 변환할 CSV 파일 경로
    output_csv = './converted_output.csv'  # 변환된 결과를 저장할 CSV 파일 경로

    convert_csv(input_csv, output_csv)
    print(f"Conversion complete. Output saved to {output_csv}")