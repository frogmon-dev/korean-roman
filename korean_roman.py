import re

"""
------------------------------------------------------------------------------
                               한글 로마자 변환기
------------------------------------------------------------------------------

Copyright (c) 2015, Kijin Sung <kijin@kijinsung.com>
All rights reserved.

This software is based on the original PHP code by Kijin Sung, and has been 
translated to Python by Frogmon Corp.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

class HangeulRomaja:
    # Constants for settings
    TYPE_DEFAULT = 0
    TYPE_NAME = 1
    TYPE_ADDRESS = 2
    CAPITALIZE_NONE = 4
    CAPITALIZE_FIRST = 8
    CAPITALIZE_WORDS = 16
    PRONOUNCE_NUMBERS = 32
    
    ordmap3 = {}  # 종성 변환 맵 (예시로 빈 값들을 채워야 합니다)
    ordmap1 = {}  # 초성 변환 맵 (예시로 빈 값들을 채워야 합니다)
    transforms_always = {}  # 항상 변환되는 자음 동화 맵 (예시로 빈 값들을 채워야 합니다)
    transforms_non_address = {}  # 주소가 아닐 때 변환되는 자음 동화 맵 (예시로 빈 값들을 채워야 합니다)    

    @staticmethod
    def convert(text, conversion_type=0, options=0):
        if text == '':
            return ''
        
        print ('Original Text = ', text)

        if conversion_type == HangeulRomaja.TYPE_NAME:
            if len(text) > 2:
                possible_surname = text[:2]
                if possible_surname in HangeulRomaja.long_surnames:
                    surname = possible_surname
                    firstname = text[2:]
                else:
                    surname = text[0]
                    firstname = text[1:]
            else:
                surname = text[0]
                firstname = text[1:]
            text = surname + ' ' + firstname
            options |= HangeulRomaja.CAPITALIZE_WORDS

        if conversion_type == HangeulRomaja.TYPE_ADDRESS:
            text = ', '.join(reversed(re.split(r'\s+', text)))
            text = re.sub(r'([동리])([0-9]+)가', r'\1 \2가', text)
            text = re.sub(r'([0-9]+)가([0-9]+)동', r' \1가 \2동', text)
            text = re.sub(r'\b(.+[로길])(.+길)\b', r'\1 \2', text)
            text = re.sub(r'([0-9]+)?([시도군구읍면동리로길가])(?=$|,|\s)', HangeulRomaja.conv_address, text)
            text = re.sub(r'([문산])로 ([0-9]+)-ga', r'\1노 \2-ga', text)
            text = text.strip()
            options |= HangeulRomaja.CAPITALIZE_WORDS

        chars = list(text)

        parts = []
        for char in chars:
            if char == '':
                continue
            elif re.match(r'[가-힣]', char):
                code = ord(char) - 44032
                part3 = code % 28
                part2 = (code // 28) % 21
                part1 = code // 28 // 21
                parts.append((1, part1))
                parts.append((2, part2))
                parts.append((3, part3))
            else:
                parts.append((0, char))

        result = []
        parts_count = len(parts)
        for i in range(parts_count):
            parttype = parts[i][0]
            part = parts[i][1]

            if parttype == 1:
                result.append(HangeulRomaja.charmap1[part])
            elif parttype == 2:
                result.append(HangeulRomaja.charmap2[part])
            elif parttype == 3:
                if i < parts_count - 1 and part > 0:
                    nextpart = parts[i + 1]
                    if nextpart[0] == 1:
                        newparts = HangeulRomaja.transform(part, nextpart[1], parttype)
                        part = newparts[0]
                        parts[i + 1] = (nextpart[0], newparts[1])
                result.append(HangeulRomaja.charmap3[part])
            else:
                result.append(part)

        # 불필요한 공백이나 반복되는 글자를 제거합니다.
        result = ''.join(result)
        result = result.replace('kkk', 'kk').replace('ttt', 'tt').replace('ppp', 'pp')
        result = re.sub(r'\s+', ' ', result)

        # 숫자 발음표현 처리를 거칩니다.
        if options & HangeulRomaja.PRONOUNCE_NUMBERS:
            if conversion_type == HangeulRomaja.TYPE_ADDRESS:
                result = ', '.join(
                    [re.sub(r'[0-9]+', HangeulRomaja.conv_number, word) if re.search(r'[a-z]', word) else word
                    for word in result.split(', ')])
            else:
                result = re.sub(r'[0-9]+', HangeulRomaja.conv_number, result)

        # 대문자 처리를 거칩니다.
        if options & HangeulRomaja.CAPITALIZE_WORDS:
            result = ' '.join([word.capitalize() for word in result.split(' ')])
        elif options & HangeulRomaja.CAPITALIZE_FIRST:
            result = result.capitalize()

        print ('Result Text = ', result)

        return result  # 변환된 결과를 반환합니다.
        
    @staticmethod
    def conv_address(match):
        if match.group(1):
            return ' ' + match.group(1) + '-' + HangeulRomaja.convert(match.group(2))
        else:
            return '-' + HangeulRomaja.convert(match.group(2))

    @staticmethod
    def conv_number(match):
        number = str(int(match.group(0)))
        pronounced = ''
        largest_place = len(number) - 1

        for i in range(largest_place + 1):
            digit = HangeulRomaja.numbers_pronunciation['digits'][int(number[i])]
            place = HangeulRomaja.numbers_pronunciation['places'][largest_place - i]
            if digit == '일' and place != '':
                digit = ''
            if digit != '영':
                pronounced += digit + place

        pronounced = HangeulRomaja.convert(pronounced)
        return f"{number}({pronounced})"

    @staticmethod
    def transform(part, next_part, part_type):
        try:
            key = HangeulRomaja.ordmap3[part] + HangeulRomaja.ordmap1[next_part]

            if key in HangeulRomaja.transforms_always:
                result_key = HangeulRomaja.transforms_always[key].replace('  ', '   ')
                result = [
                    int(HangeulRomaja.ordmap3.index(result_key[:3])),
                    int(HangeulRomaja.ordmap1.index(result_key[3:6]))
                ]
            elif part_type != HangeulRomaja.TYPE_ADDRESS and key in HangeulRomaja.transforms_non_address:
                result_key = HangeulRomaja.transforms_non_address[key].replace('  ', '   ')
                result = [
                    int(HangeulRomaja.ordmap3.index(result_key[:3])),
                    int(HangeulRomaja.ordmap1.index(result_key[3:6]))
                ]
            else:
                result = [part, next_part]

            if result[0] == 8 and result[1] == 5:
                result[1] = 19

            return result
        except ValueError:
            print(f"Error processing transform: '{key}' not found in ordmap3 or ordmap1")
            print(f"Original part: {HangeulRomaja.ordmap3[part]}, Next part: {HangeulRomaja.ordmap1[next_part]}")
            print(f"Result key: {result_key}")
            return [part, next_part]  # 기본적으로 원래 값을 반환하여 처리를 계속하도록 함

    numbers_pronunciation = {
        'digits': ["영", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"],
        'places': ["", "십", "백", "천", "만", "십만", "백만", "천만", "억"]
    }

    # 숫자 발음표현
    numbers_pronunciation = {
        'digits': ['영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'],
        'places': ['', '십', '백', '천', '만']
    }

    # 자음 동화 목록 (항상 적용)
    transforms_always = {
        'ㄱㄴ': 'ㅇㄴ',
        'ㄱㄹ': 'ㅇㄴ',
        'ㄱㅁ': 'ㅇㅁ',
        'ㄱㅇ': '  ㄱ',
        'ㄲㄴ': 'ㅇㄴ',
        'ㄲㄹ': 'ㅇㄴ',
        'ㄲㅁ': 'ㅇㅁ',
        'ㄲㅇ': '  ㄲ',
        'ㄳㅇ': 'ㄱㅅ',
        'ㄴㄹ': 'ㄹㄹ',
        'ㄴㅋ': 'ㅇㅋ',
        'ㄵㄱ': 'ㄴㄲ',
        'ㄵㄷ': 'ㄴㄸ',
        'ㄵㄹ': 'ㄹㄹ',
        'ㄵㅂ': 'ㄴㅃ',
        'ㄵㅅ': 'ㄴㅆ',
        'ㄵㅇ': 'ㄴㅈ',
        'ㄵㅈ': 'ㄴㅉ',
        'ㄵㅋ': 'ㅇㅋ',
        'ㄵㅎ': 'ㄴㅊ',
        'ㄶㄱ': 'ㄴㅋ',
        'ㄶㄷ': 'ㄴㅌ',
        'ㄶㄹ': 'ㄹㄹ',
        'ㄶㅂ': 'ㄴㅍ',
        'ㄶㅈ': 'ㄴㅊ',
        'ㄷㄴ': 'ㄴㄴ',
        'ㄷㄹ': 'ㄴㄴ',
        'ㄷㅁ': 'ㅁㅁ',
        'ㄷㅂ': 'ㅂㅂ',
        'ㄷㅇ': '  ㄷ',
        'ㄹㄴ': 'ㄹㄹ',
        'ㄹㅇ': '  ㄹ',
        'ㄺㄴ': 'ㄹㄹ',
        'ㄺㅇ': 'ㄹㄱ',
        'ㄻㄴ': 'ㅁㄴ',
        'ㄻㅇ': 'ㄹㅁ',
        'ㄼㄴ': 'ㅁㄴ',
        'ㄼㅇ': 'ㄹㅂ',
        'ㄽㄴ': 'ㄴㄴ',
        'ㄽㅇ': 'ㄹㅅ',
        'ㄾㄴ': 'ㄷㄴ',
        'ㄾㅇ': 'ㄹㅌ',
        'ㄿㄴ': 'ㅁㄴ',
        'ㄿㅇ': 'ㄹㅍ',
        'ㅀㄴ': 'ㄴㄴ',
        'ㅀㅇ': '  ㄹ',
        'ㅁㄹ': 'ㅁㄴ',
        'ㅂㄴ': 'ㅁㄴ',
        'ㅂㄹ': 'ㅁㄴ',
        'ㅂㅁ': 'ㅁㅁ',
        'ㅂㅇ': '  ㅂ',
        'ㅄㄴ': 'ㅁㄴ',
        'ㅄㄹ': 'ㅁㄴ',
        'ㅄㅁ': 'ㅁㅁ',
        'ㅄㅇ': 'ㅂㅅ',
        'ㅅㄴ': 'ㄴㄴ',
        'ㅅㄹ': 'ㄴㄴ',
        'ㅅㅁ': 'ㅁㅁ',
        'ㅅㅂ': 'ㅂㅂ',
        'ㅅㅇ': '  ㅅ',
        'ㅆㄴ': 'ㄴㄴ',
        'ㅆㄹ': 'ㄴㄴ',
        'ㅆㅁ': 'ㅁㅁ',
        'ㅆㅂ': 'ㅂㅂ',
        'ㅆㅇ': '  ㅆ',
        'ㅇㄹ': 'ㅇㄴ',
        'ㅈㅇ': '  ㅈ',
        'ㅊㅇ': '  ㅊ',
        'ㅋㅇ': '  ㅋ',
        'ㅌㅇ': '  ㅌ',
        'ㅍㅇ': '  ㅍ',
    }

    # 자음 동화 목록 (주소에서는 적용하지 않음)
    transforms_non_address = {
        'ㄴㄱ': 'ㅇㄱ',
        'ㄴㅁ': 'ㅁㅁ',
        'ㄴㅂ': 'ㅁㅂ',
        'ㄴㅍ': 'ㅁㅍ',
    }
    
    # 두 글자짜리 성씨 목록
    long_surnames = [
        '남궁',
        '독고',
        '동방',
        '사공',
        '서문',
        '선우',
        '소봉',
        '제갈',
        '황보',
    ]
    
    # 초성 목록 (번역표)
    charmap1 = [
        'g',    # ㄱ
        'kk',   # ㄲ
        'n',    # ㄴ
        'd',    # ㄷ
        'tt',   # ㄸ
        'r',    # ㄹ
        'm',    # ㅁ
        'b',    # ㅂ
        'pp',   # ㅃ
        's',    # ㅅ
        'ss',   # ㅆ
        '',     # ㅇ
        'j',    # ㅈ
        'jj',   # ㅉ
        'ch',   # ㅊ
        'k',    # ㅋ
        't',    # ㅌ
        'p',    # ㅍ
        'h',    # ㅎ
        'l',    # ㄹㄹ
    ]
    
    # 중성 목록 (번역표)
    charmap2 = [
        'a',    # ㅏ
        'ae',   # ㅐ
        'ya',   # ㅑ
        'yae',  # ㅒ
        'eo',   # ㅓ
        'e',    # ㅔ
        'yeo',  # ㅕ
        'ye',   # ㅖ
        'o',    # ㅗ
        'wa',   # ㅘ
        'wae',  # ㅙ
        'oe',   # ㅚ
        'yo',   # ㅛ
        'u',    # ㅜ
        'wo',   # ㅝ
        'we',   # ㅞ
        'wi',   # ㅟ
        'yu',   # ㅠ
        'eu',   # ㅡ
        'ui',   # ㅢ
        'i',    # ㅣ
    ]
    
    # 종성 목록 (번역표)
    charmap3 = [
        '',     # 받침이 없는 경우
        'k',    # ㄱ
        'k',    # ㄲ
        'k',    # ㄳ
        'n',    # ㄴ
        'n',    # ㄵ
        'n',    # ㄶ
        't',    # ㄷ
        'l',    # ㄹ
        'k',    # ㄺ
        'm',    # ㄻ
        'p',    # ㄼ
        't',    # ㄽ
        't',    # ㄾ
        'p',    # ㄿ
        'l',    # ㅀ
        'm',    # ㅁ
        'p',    # ㅂ
        'p',    # ㅄ
        't',    # ㅅ
        't',    # ㅆ
        'ng',   # ㅇ
        't',    # ㅈ
        't',    # ㅊ
        'k',    # ㅋ
        't',    # ㅌ
        'p',    # ㅍ
        '',     # ㅎ
    ]
    
    # 초성 목록 (순서표)
    ordmap1 = [
        'ㄱ',
        'ㄲ',
        'ㄴ',
        'ㄷ',
        'ㄸ',
        'ㄹ',
        'ㅁ',
        'ㅂ',
        'ㅃ',
        'ㅅ',
        'ㅆ',
        'ㅇ',
        'ㅈ',
        'ㅉ',
        'ㅊ',
        'ㅋ',
        'ㅌ',
        'ㅍ',
        'ㅎ',
    ]

    # 중성 목록 (순서표)
    ordmap2 = [
        'ㅏ',
        'ㅐ',
        'ㅑ',
        'ㅒ',
        'ㅓ',
        'ㅔ',
        'ㅕ',
        'ㅖ',
        'ㅗ',
        'ㅘ',
        'ㅙ',
        'ㅚ',
        'ㅛ',
        'ㅜ',
        'ㅝ',
        'ㅞ',
        'ㅟ',
        'ㅠ',
        'ㅡ',
        'ㅢ',
        'ㅣ',
    ]
    
    # 종성 목록 (순서표)
    ordmap3 = [
        '   ',  # 받침이 없는 경우
        'ㄱ',
        'ㄲ',
        'ㄳ',
        'ㄴ',
        'ㄵ',
        'ㄶ',
        'ㄷ',
        'ㄹ',
        'ㄺ',
        'ㄻ',
        'ㄼ',
        'ㄽ',
        'ㄾ',
        'ㄿ',
        'ㅀ',
        'ㅁ',
        'ㅂ',
        'ㅄ',
        'ㅅ',
        'ㅆ',
        'ㅇ',
        'ㅈ',
        'ㅊ',
        'ㅋ',
        'ㅌ',
        'ㅍ',
        'ㅎ',
    ]