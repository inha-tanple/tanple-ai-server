# time_date_recog_code.py

""""
input: img_path 위치
    img_path = '영수증_가본2.png'
    
    
output: Receipt class

    self.date = ""
    self.time_str = ""
    
    output ex)
    날짜: 2024-05-20
    시간: 17:21:25

"""



import cv2
import numpy as np
from scipy.ndimage import interpolation as inter
import re
from collections import defaultdict
import imutils
from imutils.perspective import four_point_transform
from paddleocr import PaddleOCR

import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'



# input #################################################################
img_path = "KakaoTalk_20240605_150513168.jpg"



original_img = cv2.imread(img_path)
image = original_img.copy()



# sharpen -> blur -> edge: filter
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
sharpen_filter = np.array([[-1,-1,-1],[-1,9,-1], [-1,-1,-1]])
sharpen = cv2.filter2D(gray, -1, sharpen_filter)
blurred_sharpen = cv2.GaussianBlur(sharpen, (9,9), 0)
edged_sharpen = cv2.Canny(blurred_sharpen, -75, 200)



# contour 찾기
cnts = cv2.findContours(edged_sharpen.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

height, width = image.shape[:2]
max_area = height * width
min_contour_area = max_area/4

receiptCnt = None
for c in cnts:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)

    if len(approx) == 4:
        receiptCnt = approx
        break
    
# print("max area: ", max_area)
# print("min_contour: " , min_contour_area)
# print("contour area: ",cv2.contourArea(receiptCnt))


receipt = image.copy()
# 인식된 contour가 잘못 인식되었을 때
def receiptCnt_process():
    if receiptCnt is None:
        # print("Could not find outline")
        return False

    elif cv2.contourArea(receiptCnt) < min_contour_area:
        # print("contour is too small****************")
        return False

    return True

if receiptCnt_process():
    output = image.copy()
    cv2.drawContours(output, [receiptCnt], -1, (255, 0, 0), 3)

    # 해당 영역
    ratio = original_img.shape[1] / float(image.shape[1])
    receipt = four_point_transform(original_img, receiptCnt.reshape(4, 2) * ratio)
    
    
    
# 기울어진 영수증 똑바르게
def correct_skew(image, delta=1, limit=10):  # limit이 얼마일지 정해야함. 시간, 정확도 고려해서
    def determine_score(arr, angle):
        data = inter.rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return histogram, score

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] 

    scores = []
    angles = np.arange(-limit, limit + delta, delta)
    for angle in angles:
        histogram, score = determine_score(thresh, angle)
        scores.append(score)

    best_angle = angles[scores.index(max(scores))]

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    corrected = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return best_angle, corrected





angle, corrected = correct_skew(receipt)
print('Skew angle:', angle)
# ocr 돌리는 최종 이미지 : corrected
# cv2.imshow('corrected', corrected)
# cv2.waitKey()
# cv2.destroyAllWindows()



# ocr #################################################################
ocr = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=False)  # gpu 사용하면 수정**
result = ocr.ocr(corrected, cls=True)
data = []
for idx in range(len(result)):
    res = result[idx]
    for line in res:
        # print(line)
        data.append(line)

def group_text_lines(data, grouping_interval):
    lines = defaultdict(list)
    
    for item in data:
        coords, (text, _) = item
        y = np.mean([coord[1] for coord in coords])
        lines[int(y // grouping_interval) * grouping_interval].append((coords, text))
    
    sorted_lines = []
    
    for y in sorted(lines.keys()):
        line = lines[y]
        line.sort(key=lambda x: x[0][0][0])
        sorted_line = ' '.join([text for _, text in line])
        sorted_lines.append(sorted_line)
    
    return sorted_lines

sorted_lines = group_text_lines(data, 20)
for line in sorted_lines:
    print(line)



# 빠른 test (위에 다 주석처리 import 제외)
# sorted_lines = ['영수중', '이마트 연수점', '인천 연수구 ``래공은 184', '상품명 단가 수량 - 농본----', '01 참그린 독차 14L 4300 - 4300', '02 자연벽지6002 70000 140000', '과세물품 130300', '부%가6세 14000', '총합계 144300', 'I 공루 -0', 'ㄹ속Io공루 -0', '결제대상금액 144300', '- -', '[신용 - 카드 승인]', '승 弓공 - 시 2024-05-20 17:21:25', '카드번 - 532750******6111', '할부개월:', '승 6 29705902 00', '인금 145500', '- 호 00919 9032590 하나카드', '2024-05-20 17:21']
#sorted_lines=['매출 천표 고객용/ /가맹점용', '신용!승인', '24-05-21 16:38:5/', '9445 2024C', '년/원 **/**', '00045328769', '|E', '홈 3000 1955', 'K국민카드 전자서명전표', '51 819원', '각치세 5 181', '0분', '미 57 000원', '1211697138', '자륙자령 TEL:032 8680220', '주조:인천 미추홀구 인하로 89-1 용현동', '전표N0:2405432731', 'CAIID: 13****32/E113CYL', '저명 052107844473']



date = ""
time_str = ""


for line in sorted_lines:
    # date
    if re.search(r'\d{2}', line):
        sign = False
        match1 = re.search(r'(20\d{2})\s*?-?\s*?(\d{2})\s*?-\s*?(\d{2})', line)   # 2024 05-13 또는 2024-05-13 
        match2 = re.search(r'(20\d{2})\s*(\d{2})\s*(\d{2})', line)  # 20240513
        match3 = re.search(r'(\d{2})\s*?-\s*?(\d{2})\s*?-\s*?(20\d{2})', line)   # 12-31-2024
        match4 = re.search(r'(\d{2})\s*?-\s*?(\d{2})\s*?-\s*?(\d{2})', line)   # 24-05-12
        if match1:
            if len(match1.groups()) == 3:
                year = match1.group(1)
                month = int(match1.group(2))
                day = int(match1.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    date = f"{year}-{month:02d}-{day:02d}"
        elif match3:
            if len(match3.groups()) == 3:
                month = int(match3.group(1))
                day = int(match3.group(2))
                year = match3.group(3)
                if 1 <= month <= 12 and 1 <= day <= 31: 
                    date = f"{year}-{month:02d}-{day:02d}"
        elif match4:
            if len(match4.groups()) == 3:
                year = int(match4.group(1))
                month = int(match4.group(2))
                day = int(match4.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31: 
                    year = f"20{year:02d}" 
                    date = f"{year}-{month:02d}-{day:02d}"
        elif match2:
            if len(match2.groups()) == 3:
                year = match2.group(1)
                month = int(match2.group(2))
                day = int(match2.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31: 
                    date = f"{year}-{month:02d}-{day:02d}"
                    
                
    # time
    if re.search(r'\d{2}', line):
        if time_str == "":
            hh = mm = ss = -1
            
            match1 = re.search(r'(^|[^a-zA-Z0-9])(\d{2})\s*:\s*(\d{2})\s*:\s*(\d{2})($|[^a-zA-Z0-9])', line)
            match2 = re.search(r'(^|[^a-zA-Z0-9])(\d{2})\s*:\s*(\d{2})($|[^a-zA-Z0-9])', line)
            if match1:
                hh = int(match2.group(2))
                mm = int(match2.group(3))
                ss = int(match2.group(4))
                if 0 <= hh <= 24 and 0 <= mm  <= 59 and 0 <= ss <= 59: 
                    time_str = f"{hh:02d}:{mm:02d}:{ss:02d}"
            elif match2:
                hh = int(match2.group(2))
                mm = int(match2.group(3))
                ss = 0
                if 0 <= hh <= 24 and 0 <= mm  <= 59 and 0 <= ss <= 59: 
                    time_str = f"{hh:02d}:{mm:02d}:{ss:02d}"
    
    
    if time_str != "" and date != "":
        break


# output #################################################################
# 클래스 객체 생성
class Receipt:
    def __init__(self):
        self.date = ""
        self.time_str = ""


r1 = Receipt()
r1.date = date
r1.time_str = time_str

    
# print("날짜:", r1.date)
# print("시간:", r1.time_str)
