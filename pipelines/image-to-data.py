# image-to-data.py

""""
input: img_path 위치
    img_path = '영수증_가본2.png'
    
    
output: Receipt class

    self.store = ""
    self.location = ""
    self.date = ""
    self.time_str = ""
    self.items = []   ->   dictionary
        { 'item_number': item_number,
        'description': description,
        'unit_price': unit_price,
        'quantity': quantity,
        'amount': amount }

    self.total_amount = 0 
    self.card_number = ""
    self.approval_number = ""
    
    output ex)
    
    가게: 이마트 연수점
    위치: 인천 연수구 래공은 184
    날짜: 2024-05-20
    시간: 17:21:25
    상품들: [{'item_number': '01', 'description': '참그린 독차 14L', 'unit_price': 4300, 'quantity': 1, 'amount': 4300}, {'item_number': '02', 'description': '자연벽지6002', 'unit_price': 70000, 'quantity': 2, 'amount': 140000}]
    총 금액: 144300
    카드 번호: 532750******6111
    승인 번호:
    time : 65.077223777771


"""





import os
import time
from paddleocr import PaddleOCR,draw_ocr
from collections import defaultdict
import numpy as np
from PIL import Image
import re


# OMP: Error #15 해결해려고
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# time
# start = time.time()


img_path = '영수증_가본2.png'


ocr = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=False)  # gpu 사용하면 수정**
result = ocr.ocr(img_path, cls=True)
data = []
for idx in range(len(result)):
    res = result[idx]
    for line in res:
        # print(line)
        data.append(line)


# 줄 단위로 나누기
lines = defaultdict(list)
for item in data:
    coords, (text, _) = item
    y = np.mean([coord[1] for coord in coords]) 
    lines[int(y // 10) * 10].append((coords, text))
sorted_lines = []
for y in sorted(lines.keys()):
    line = lines[y]
    line.sort(key=lambda x: x[0][0][0])
    sorted_line = ' '.join([text for _, text in line])
    sorted_lines.append(sorted_line)
    
    
    
# 결과 출력
print("--------------------------------")
for line in sorted_lines:
    print(line)
print("--------------------------------")




# 빠른 test (위에 다 주석처리 import 제외)
# sorted_lines = ['영수중', '이마트 연수점', '인천 연수구 래공은 184', '상품명 단가 수량 - 농본----', '01 참그린 독차 14L 4300 - 4300', '02 자연벽지6002 70000 140000', '과세물품 130300', '부%가6세 14000', '총합계 144300', 'I 공루 -0', 'ㄹ속Io공루 -0', '결제대상금액 144300', '- -', '[신용 - 카드 승인]', '승 弓공 - 시 2024-05-20 17:21:25', '카드번 - 532750******6111', '할부개월:', '승 6 29705902 00', '인금 145500', '- 호 00919 9032590 하나카드', '2024-05-20 17:21']



# 클래스 객체 생성
class Receipt:
    def __init__(self):
        self.store = ""
        self.location = ""
        self.date = ""
        self.time_str = ""
        self.items = []
        self.total_amount = 0
        self.card_number = ""
        self.approval_number = ""


store = ""
location = ""
date = ""
time_str = ""
items = []
total_amount = 0
total_amount_check = 0
card_number = ""
approval_number = ""

loc_pattern = re.compile(r'^(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충남|충북|전북|전남|경북|경남|제주)')
loc2_pattern = re.compile(r'(마트)')
pattern = re.compile(r'(카|드).*?(드|번).*?(번|호).*')
pattern2 = re.compile(r'(승|인).*?(인|번).*?(번|호).*')
pattern3 = re.compile(r'(총|합).*?(합|계).*')
pattern4 = re.compile(r'(상품명|단가|수량).*?(단가|수량|금액).*')
pattern5 = re.compile(r'\b\d+\b \b\d+\b \b\d+\b$')
pattern6 = re.compile(r'^(.*?) (\d+) (\d+) (\d+)$')
pattern7 = re.compile(r'^(\d{2})\s+(.*?)\s+(-?\d+)\s+(-?\d+)?')
pattern8 = re.compile(r'^(\d{2})\s+(.*?)\s+(-?\d+)\s+(.*)?\s+(-?\d+)?')
item_sign = False


for line in sorted_lines:
    if item_sign:
        if re.findall(r'^(\d{2})', line):
            item_number = ""
            description = ""
            unit_price = 0
            quantity = 0
            amount = 0
            
            matches1 = re.findall(pattern7, line)
            matches2 = re.findall(pattern8, line)
            # print(matches1)
            # print(matches2)
            if matches2:
                for match in matches2:
                    item_number = match[0]
                    description = match[1].strip()
                    unit_price = int(match[2]) 
                    quantity = match[3]
                    amount =  int(match[4])
                    
                if amount < 0 :
                    amount = -amount
                if unit_price < 0 :
                    unit_price = -unit_price
                    
                if ((amount // unit_price) != (amount / unit_price)):
                    amout = 0  
                elif (unit_price and amount and unit_price) != 0 and ((amount // unit_price) == (amount / unit_price)):
                    quantity = amount // unit_price
                else:
                    quantity = 1  # 기본값 설정
                        
                total_amount_check += amount
            else:
                for match in matches1:
                    item_number = match[0]
                    description = match[1].strip()
                    unit_price = int(match[2]) 
                    amount =  int(match[3])
                    
                if amount < 0 :
                    amount = -amount
                if unit_price < 0 :
                    unit_price = -unit_price
                    
                if unit_price and amount and unit_price != 0 and amount // unit_price == amount / unit_price:
                        quantity = amount // unit_price
                else:
                    quantity = 1  # 기본값 설정    
                
                total_amount_check += amount
                
            items.append({
                'item_number': item_number,
                'description': description,
                'unit_price': unit_price,
                'quantity': quantity,
                'amount': amount
            })
    if loc_pattern.match(line):
        item_sign = False
        location = line
    elif re.findall(loc2_pattern, line):
        item_sign = False
        store = line
    elif re.findall(pattern, line):
        item_sign = False
        pat = re.compile(r'[\d*]+')
        matches = pat.findall(line)
        card_number = ''.join(matches)
    elif re.findall(pattern2, line):
        item_sign = False
        words = line.split()
        a = False
        for w in words:
            if a == True:
                pat = re.compile(r'[\d]+')
                if not re.findall(pat, w):
                    break
                else:
                    approval_number += w
            else:
                if '호' in w:
                    a = True
    elif re.findall(pattern3, line):
        words = line.split()
        total_amount = words[1]
    elif re.findall(pattern4, line):
        item_sign = True
            
    
    if re.search(r'\d{4}-\d{2}-\d{2}', line):
        date = re.search(r'\d{4}-\d{2}-\d{2}', line).group()
    if re.search(r'\d{2}:\d{2}:\d{2}', line):
        time_str = re.search(r'\d{2}:\d{2}:\d{2}', line).group()


r1 = Receipt()
r1.store = store
r1.location = location
r1.date = date
r1.time_str = time_str
r1.items = items
if int(total_amount_check) == int(total_amount):
    r1.total_amount = total_amount
else:
    r1.total_amount = 0
r1.card_number = card_number
r1.approval_number = approval_number

    
print("가게:", r1.store)
print("위치:", r1.location)
print("날짜:", r1.date)
print("시간:", r1.time_str)
print("상품들:", r1.items)
print("총 금액:", r1.total_amount)
print("카드 번호:", r1.card_number)
print("승인 번호:", r1.approval_number)


# draw result
# image = Image.open(img_path).convert('RGB')
# boxes = [line[0] for line in result[0]]
# txts = [line[1][0] for line in result[0]]
# scores = [line[1][1] for line in result[0]]
# im_show = draw_ocr(image, boxes, txts, scores, font_path='C:\WINDOWS\FONTS\GULIM.TTC')
# im_show = Image.fromarray(im_show)
# im_show.save('result0.jpg')  # 이미지로 저장


# print("time :", time.time() - start) 