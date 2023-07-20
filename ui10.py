import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import cv2
#UI 관련 import1
from enum import auto
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import pyzbar.pyzbar as pyzbar
import numpy as np
from playsound import playsound
import time
from datetime import datetime
import shutil
import os
import json
import re
from final8 import first
import tracemalloc
from memory_profiler import profile
import random
#############################################
#여기서 에러 일어남 처리 요청                   #
#############################################


cred = credentials.Certificate('./key.json')
firebase_admin.initialize_app(cred,{
    'databaseURL' : 'https://signfiftyoneman-default-rtdb.asia-southeast1.firebasedatabase.app/' 
    #'databaseURL' : '데이터 베이스 url'
})
cnt = 0


################################
# this part is modified due to camera issue 
################################
#camera = cv2.imread('test2.png', cv2.IMREAD_COLOR)
camera = cv2.VideoCapture(0)
# global_uid = 0

class Logincam(QThread):
    uidout = pyqtSignal(str)
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.cap = camera
        self.running = True
        self.uid = None
        self.pre = None
        self.now = None
        self.domessage=False
    
    def run(self):
        while self.running:
            ret, img = self.cap.read()
            if ret:
                decodeObjects = self.decode(img)
                # image_test = cv2.imread('./test2.png', cv2.IMREAD_COLOR)
                # decodeObjects = self.decode(image_test)
                ############################################
                # 자동 로그인 풀려면 위 두줄 지우고 위에주석풀기  #
                ############################################
                
                self.display(img, decodeObjects)
                

            img = cv2.flip(img, 1)
            h,w = img.shape[:2]
            #h_label, w_habel = self.parent.label.size()
            #image = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            #image_resize = cv2.resize(img, dsize=(0,0), fx=self.parent.label.size().width()/w, fy=self.parent.label.size().height()/h,interpolation=cv2.INTER_LINEAR)
            #image_resize = cv2.cvtColor(image_resize,cv2.COLOR_BGR2RGB)
            #qt_img = QImage(image_resize, self.parent.label.size().width(), self.parent.label.size().height(), QImage.Format_RGB888)
            image = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            qt_img = QImage(image, w, h, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qt_img)
            #p = pix.scaled(int(w*self.parent.label.size().height()/h),self.parent.label.size().height(),Qt.IgnoreAspectRatio) 
            #p = pix.scaled(1280,960,Qt.IgnoreAspectRatio) 

            self.parent.label.setPixmap(pix)
            # if self.uid is not None:
            #     print(datetime.now(), "thread send user_id : ", self.uid)
            
            self.finduid()
            
            # loop = QEventLoop()
            # QTimer.singleShot(25, loop.quit) #25 ms
            # loop.exec_()

    def decode(self, im):
        decodedObjects = pyzbar.decode(im)
        for obj in decodedObjects: 
            # print('Type : ', obj.type) 
            # print('Data : ', obj.data, '\n')

            self.uid = (obj.data.decode("utf-8"))
            # playsound("grbarcode_beep.mp3")
        return decodedObjects

    def display(self, im, decodedObjects):
        for decodedObject in decodedObjects: 
            points = decodedObject.polygon

            if len(points) > 4: 
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32)) 
                hull = list(map(tuple, np.squeeze(hull))) 
            else: 
                hull = points

            n = len(hull)

            for j in range(0, n): 
                cv2.line(im, hull[j], hull[(j + 1) % n], (255, 0, 0), 3)

        

    def finduid(self):
        self.now = self.uid
        if self.now != self.pre:
            ref = db.reference('List of Users')
            if self.now in ref.get():
                # print("key exist")
                ref2 = ref.child(self.now)
                self.parent.stackedWidget.setCurrentIndex(1)
                self.parent.capcam.allergy = ref2.get()['allergy']
                # print("allergy : "+self.parent.capcam.allergy)
                self.uidout.emit(self.now)
                self.parent.stackedWidget.setCurrentIndex(1)
                self.parent.label_17.setText("상품의 성분표를 카메라에 가져다 댄 후 촬영 버튼을 눌러 촬영해주세요")
                self.pause()
                self.parent.capcam.resume()
                self.parent.capcam.start()

            else:
                # print("key not exit")
                # self.domessage=True
                
                # errorMsg = '로그인 실패'
                # QMessageBox.about(self.parent,"실패",errorMsg)
                # time.sleep(1)
                test=1
     
        self.pre = self.uid
        #self.Domessage()

    def Domessage(self):
        if self.domessage==True:
            errorMsg = '로그인 실패'
            # print(errorMsg)
            QMessageBox.about(None,"실패",errorMsg)
        self.domessage=False

    def resume(self):
        self.running = True

    def pause(self):
        self.running = False


class Capcam(QThread):
    camout = pyqtSignal()
    @profile
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.cap = camera
        self.StartSetting()
        self.running = True
        self.ret = None
        self.img = None
        self.Buyitem = []
        self.BuyitemNum = 0
        self.now = -1
        self.abc = first()
        self.nutri = ""
        self.total_nutrition = ""
        self.Fileclear()
        self.allergy = ""
        self.allergywarning = 0
        self.ingrelist = []
        self.Addingrelist()
        self.Buyitemingrelist = []
        self.recommend = ""
        self.Onemorepicture = False
        self.recommendingredient = ""
        self.recommendurl = ""


        # self.add_nutritional = open('./add_nutritional_info.txt','r')
        
    def Addingrelist(self):
        file123 = open('./ingredientlist.txt', 'r')
        lines = file123.readlines()
        for line in lines:
            if line == '\n':
                lines.remove(line)
                
        for item in lines:
            self.ingrelist.append(item.strip('\n'))
        file123.close()
     
        
    def Fileclear(self):
        fi = open('./nutritional_info.txt','w')
        fi.write(" ")
        fi.close()
    
    def run(self):
        while self.running:
            ret, img = self.cap.read()
            self.ret, self.img = ret, img
            h,w = img.shape[:2]
            image = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            qt_img = QImage(image, w, h, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qt_img) 
            # p = pix.scaled(int(w*self.parent.label_3.size().height()/h),self.parent.label_3.size().height(),Qt.IgnoreAspectRatio)
            #p = pix.scaled(960,680,Qt.IgnoreAspectRatio)
            self.parent.label_3.setPixmap(pix)
            
            #loop = QEventLoop()
            #QTimer.singleShot(25, loop.quit) #25 ms
            #loop.exec_()
            #이게 QBasicTime인지 확인하려고 주석했음
            
    def resume(self):
        self.running = True

    def pause(self):
        self.running = False


        

    def StartSetting(self):
        #버튼 관련 함수 연결
        self.parent.pushButton.clicked.connect(self.Capture)
        self.parent.pushButton.clicked.connect(self.ProductPage)
        self.parent.pushButton_4.clicked.connect(self.PhotoPage)
        self.parent.pushButton_3.clicked.connect(self.StackedPage)
        self.parent.pushButton_2.clicked.connect(self.Additem)
        self.parent.pushButton_6.clicked.connect(self.PhotoPage)
        self.parent.pushButton_7.clicked.connect(self.Re_LoginPage)
        self.parent.pushButton_10.clicked.connect(self.Next)
        self.parent.pushButton_11.clicked.connect(self.Before)
        self.parent.pushButton_12.clicked.connect(self.Deleteitem)
        self.parent.pushButton_5.clicked.connect(self.Recommend)
        
    def Recommend(self):
        
        ######################식단 추천 알고리즘 3번째##########################

        path_to_json = './recipes_file' # 후에 json 파일들이 있는 폴더로 위치를 설정해 줄 것
        finding = self.Buyitemingrelist # 나중에 입력을 받아서 그 입력대로 실행할 것
        recommendation = [0] # 여기에 추천되는 식단들 저장
        count = 0

        json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')] # json 파일을 읽어옴
        for pos_json in json_files:
            with open(path_to_json+'/'+pos_json,'r', encoding = 'CP949') as f:
                try:
                    json_data = json.load(f)
                except:
                    f.close()
                    f = open(path_to_json+'/'+pos_json,'a')
                    f.write('}')
                    f.close()
                    continue
                count = 0
                for item in json_data['ingre_list']: # json 파일의 ingre_list -> ingre_name 이 finding의 항목과 일치하면 , 재료를 샀다면 count +1
                    if item['ingre_name'] in finding :
                        count += 1

                # 가장 많은 count를 얻은 식단을 recommendation 에 저장
                if recommendation[0] == count :
                    recommendation.append({json_data['name']:json_data['id']})
                elif recommendation[0] < count :
                    recommendation = []
                    recommendation.append(count)
                    recommendation.append({json_data['name']:json_data['id']})
            f.close()
        length = len(recommendation)
        dictionary = recommendation[random.randrange(1,length)]
        self.recommend = next(iter(dictionary))
        filenumber = dictionary.get(self.recommend)
        with open(path_to_json+'/'+filenumber+'.json','r', encoding = 'CP949') as f2:
            try:
                json_data = json.load(f2)
                for item in json_data['ingre_list']:
                    self.recommendingredient = self.recommendingredient+'\n'+item['ingre_name']
                self.recommendurl =  json_data['url']
                f2.close()
            except:
                f2.close()
                self.recommendingredient = ""
                self.recommendurl = ""
        
        self.parent.stackedWidget.setCurrentIndex(5)
        self.parent.label_10.setText(self.recommend)
        self.parent.label_11.setText(self.recommendingredient)
        self.parent.label_12.setText(self.recommendurl)
        
    def Re_LoginPage(self):
        # self.parent.logincam.now = None
        # self.parent.stackedWidget.setCurrentIndex(0)
        # self.parent.logincam.exit() 
        # self.exit()
        # self.parent.__init__()
        # print(self)

        ################################
        #   누적/1일 평균 데이터 저장   #   
        ################################

        fin = open('./add_nutritional_info.txt','r')
        data=fin.readlines()

        ref = db.reference('List of Users')
        # a=1
        # if self.abcd.now in ref.get():

        past_month = past_day = ''

        users_ref = ref.child(self.parent.logincam.uid)
        past_month = users_ref.get()['month']
        past_day = users_ref.get()['day']

        now = datetime.now()
        
        if past_day == '':
            div = 7

        else:
            past_month_num = int(past_month)
            past_day_num = int(past_day)

            if (now.day - past_day_num) < 7:
                div = now.day - past_day_num
                ## 디버그용
                if div == 0 :
                    div = 10
            else:
                div = 7

        for line in data:
            if "나트륨" in line and "g" in line:
                nutrient="natryum"
                nutrient_name="나트륨"
            elif "탄수화물" in line and "g" in line:
                nutrient="tansu"
                nutrient_name="탄수화물"
            elif "당류" in line and "g" in line:
                nutrient="dangryu"
                nutrient_name="당류"
            elif "트랜스지방" in line and "g" in line:
                nutrient="transzibang"
                nutrient_name="트랜스지방"
            elif "포화지방" in line and "g" in line:
                nutrient="powhazibang"
                nutrient_name="포화지방"
            elif "지방" in line and "g" in line:
                nutrient="zibang"
                nutrient_name="지방"
            elif "콜레스테롤" in line and "g" in line:
                nutrient="cholesterol"
                nutrient_name="콜레스테롤"
            elif "단백질" in line and "g" in line:
                nutrient="danbaek"
                nutrient_name="단백질"
            elif "칼로리" in line and "kcal" in line:
                nutrient="kcal"
                nutrient_name="칼로리"    
            else:
                continue

            if re.search("[0-9]\s*mg",line):
                amount=re.search('{}(.+?)mg'.format(nutrient_name),line).group(1)
                amount_num = float(amount)
                # print('!{}: {}mg'.format(nutrient,amount_num*self.multiple),end=" ")
            elif re.search("[0-9]\s*g",line):
                amount=re.search('{}(.+?)g'.format(nutrient_name),line).group(1)
                amount_num = float(amount)
            elif re.search("[0-9]\s*kcal",line):
                amount=re.search('{}(.+?)kcal'.format(nutrient_name),line).group(1)
                amount_num = float(amount)    
                # print('!{}: {}g'.format(nutrient,amount_num*self.multiple),end=" ")
            else:
                #에러삽입 (숫자누락 혹은 해석불가, 영양소:nutrient, 파일: json)
                #아래코드 삭제할것
                error_catch = -1

            users_ref.update({
                nutrient: {
                    'accrued': amount_num,
                    'oneday': round(amount_num/div,1)
                }
            })

        users_ref.update({
                'month': now.month,
                'day': now.day
            })

        fin.close()

        ################################
        #   누적/1일 평균 데이터 저장   #   
        ################################
        
        
        ################################
        #            파일 삭제          #   
        ################################
        try :
            os.remove('./first_process.txt')
            os.remove('./inferText2.txt')
            os.remove('./nutritional_info.txt')
        except :
            error = 1
        ################################
        #            파일 삭제          #   
        ################################


        self.pause()
        self.wait(3000)
        self.parent.stackedWidget.setCurrentIndex(6)
        self.parent.logincam.uid=None
        self.parent.logincam.now=None
        self.parent.logincam.resume()
        self.parent.logincam.start()
        ############################
        # This part needs to be modified 
        ############################

        
    
    def Subtract_nutrition(self):
        product_int = self.now + 1
        with open('./nutritional_info.txt','r') as fin:
            data = fin.read().splitlines(True)
        with open('./nutritional_info.txt','w') as fout:
            fout.writelines(data[:product_int-1])
            fout.writelines(data[product_int:])
        fin.close()
        fout.close()
        self.abc.add()
    
    def Total_nutrition(self):
        self.total_nutrition = ""
        fin = open('./add_nutritional_info.txt','r')
        data = fin.readlines()
        for line in data:
            self.total_nutrition = self.total_nutrition + line.replace('000.0mg', 'g\n').replace('mg','mg\n').replace('kcal','kcal\n')
        #self.total_nutrition.replace('mg', 'mg\n')
        fin.close()
        
                    
    
    def Additem(self):
        if not self.Onemorepicture :
            self.abc.add()
            self.Buyitem.append(self.nutri)
            shutil.copy("./test.png", "./testItemNum"+str(self.BuyitemNum)+".png")
            self.BuyitemNum += 1
            self.Addbuyingrelist()
            buttonReply = QMessageBox.information(None, '추가 사진 등록', "식단 추천을 위해 추가 사진을 등록하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
            if buttonReply == QMessageBox.Yes :
                self.Onemorepicture = True
            else :
                self.Onemorepicture = False
            self.PhotoPage()
        else :
            self.Addbuyingrelist()
            buttonReply = QMessageBox.information(None, '추가 사진 등록', "식단 추천을 위해 추가 사진을 등록하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
            if buttonReply == QMessageBox.Yes :
                self.Onemorepicture = True
            else :
                self.Onemorepicture = False
            self.PhotoPage()
    
    def Addbuyingrelist(self):
        
        self.abc.ingredient()
        if self.abc.ingredientlist == []:
            pass
        else :
            for item in self.abc.ingredientlist:
                if item in self.ingrelist:
                    self.Buyitemingrelist.append(item)
    
    def Deleteitem(self):
        if self.now == -1 or self.now == self.BuyitemNum:
            self.NoPage()
        elif self.now == self.BuyitemNum-1 :
            self.Buyitem.pop(self.now)
            self.Subtract_nutrition()
            self.now -= 1
            self.BuyitemNum -= 1
            self.StackedPage()
        else :
            self.Buyitem.pop(self.now)
            self.Subtract_nutrition()
            for i in range(1, self.BuyitemNum - self.now):
                shutil.move("./testItemNum"+str(self.now+i)+".png", "./testItemNum"+str(self.now+i-1)+".png")
            self.now -= 1
            self.BuyitemNum -= 1
            self.Next()
        
    def StackedPage(self):
        if not self.BuyitemNum:
            self.NoPage()
            
        elif self.now == -1 :
            self.Total_nutrition()
            self.parent.stackedWidget.setCurrentIndex(3)
            self.parent.label_6.setText("전체 영양성분\n 정보 페이지 입니다")
            self.parent.label_6.setFont(QFont("맑은 고딕", 20))
            self.parent.label_13.setText("전체 영양성분 정보 페이지")
            # image_2 = cv2.imread("./foodimage.png", cv2.IMREAD_COLOR)
            # h,w = image_2.shape[:2]
            # image_2 = cv2.cvtColor(image_2,cv2.COLOR_BGR2RGB)
            # qt_img = QImage(image_2, w, h, QImage.Format_RGB888)
            # pix = QPixmap.fromImage(qt_img) 
            # self.parent.label_14.setPixmap(pix)
            self.parent.label_14.setText(self.total_nutrition)
            self.parent.label_14.setFont(QFont("맑은 고딕", 20))
            self.parent.label_14.setAlignment(Qt.AlignCenter)
        else:
            self.parent.stackedWidget.setCurrentIndex(3)
            self.parent.label_6.setText(self.Buyitem[self.now])
            self.parent.label_6.setFont(QFont("맑은 고딕", 20))
            self.parent.label_13.setText("현재 페이지 :"+str(self.now+1)+"/ 총 페이지 : "+str(self.BuyitemNum))
            image_2 = cv2.imread("./testItemNum"+str(self.now)+".png", cv2.IMREAD_COLOR)
            h,w = image_2.shape[:2]
            image_2 = cv2.cvtColor(image_2,cv2.COLOR_BGR2RGB)
            qt_img = QImage(image_2, w, h, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qt_img) 
            self.parent.label_14.setPixmap(pix)

    def NoPage(self):
        self.parent.stackedWidget.setCurrentIndex(3)
        self.parent.label_6.setText('NO ITEM')
        self.parent.label_6.setFont(QFont("맑은 고딕", 20))
        self.parent.label_6.setAlignment(Qt.AlignCenter)
        self.parent.label_13.setText("해당 페이지가 존재하지 않습니다.")
        self.parent.label_14.setText("NO IMAGE")
        self.parent.label_14.setFont(QFont("맑은 고딕", 20))
        self.parent.label_14.setAlignment(Qt.AlignCenter)

    def Next(self):
        if self.now >= self.BuyitemNum-1 :
            self.NoPage()
            self.now = self.BuyitemNum
        else :
            self.now += 1
            self.StackedPage()

    def Before(self):
        if self.now <= 0 :
            self.now = -1
            self.StackedPage()
        else :
            self.now -= 1
            self.StackedPage()
        
    def PhotoPage(self):
        self.parent.stackedWidget.setCurrentIndex(1)
        if self.Onemorepicture == True:
            self.parent.label_17.setText("상품의 유형 및 추가 정보를 인식해주세요")
        else:
            self.parent.label_17.setText("상품의 성분표를 카메라에 가져다 댄 후 촬영 버튼을 눌러 촬영해주세요")
            
        self.now = -1
        
    def ProductPage(self):
        self.parent.stackedWidget.setCurrentIndex(2)
        image_2 = cv2.imread('./test.png', cv2.IMREAD_COLOR)
        h,w = image_2.shape[:2]
        image_2 = cv2.cvtColor(image_2,cv2.COLOR_BGR2RGB)
        qt_img = QImage(image_2, w, h, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img) 
        self.parent.label_4.setPixmap(pix)

        
        #################################
        # this part is for ocr
        #################################
        if not self.Onemorepicture :
            nut_info=open('./nutritional_info.txt','r', encoding = "utf8")
            self.nutri = nut_info.readlines()[self.now]
            self.nutri = self.nutri.replace('!','\n')
            self.nutri = self.nutri.replace('칼로리','\n칼로리')
            #self.nutri = self.nutri.replace('끝', '')
            self.parent.label_5.setText(self.nutri)
            self.parent.label_5.setFont(QFont("맑은 고딕", 20))
            nut_info.close()
        else :
            self.parent.label_5.setText("식단 추천을 위한 \n추가 사진촬영 \n페이지 입니다.")
            self.parent.label_5.setFont(QFont("맑은 고딕", 20))

    def Capture(self):
        if self.ret and not self.Onemorepicture:
            cv2.imwrite('./test.png', self.img)
            self.abc.__init__()
            self.abc.clova()
            self.abc.level()
            self.abc.wrongocr()
            self.abc.process()
            self.abc.extraction()
            self.abc.info()
            allergy = self.DetectAllergy()
            for item in allergy:
                if item in self.allergy:
                    self.AllergyWarning()
                    break
                
        elif self.ret and self.Onemorepicture :
            cv2.imwrite('./test.png', self.img)
            self.abc.__init__()
            self.abc.clova()
            self.abc.level()
            self.abc.ingredient()
            allergy = self.DetectAllergy()
            for item in allergy:
                if item in self.allergy:
                    self.AllergyWarning()
                    break
            
    
    def AllergyWarning(self):
        # msg = QMessageBox()
        # msg.setIcon(QMessageBox.Critical)
        # msg.setText("알러지 발견")
        # msg.setInformativeText("알러지를 발견했습니다")
        # msg.setWindowTitle("Allergy Detected")
        # msg.exec_()
        AllergyResponse = QMessageBox.information(None, '알러지 발견', "알러지를 발견했습니다, 주의하십시오", QMessageBox.Yes)
            
    def DetectAllergy(self):
        output_file = './output1.json'

        with open(output_file, 'r', encoding='utf-8') as f:
            json_object = json.load(f)


        allergic = ['메밀','대두','호두','땅콩', '잣', '계란','난류',
                    '우유','닭고기','쇠고기','돼지고기','새우','게','고등어',
                    '오징어','복숭아','토마토','아황산','조개류',
                    '굴','전복','홍합']


        detect = []

        for images in json_object['images']:
            for key in images['fields']:

                for i in allergic:
                    if (i in key['inferText']) and (i not in detect):
                        detect.append(i)


        for images in json_object['images']:
            for key in images['fields']:

                if ('밀' in key['inferText']) and ('메밀' not in key['inferText'] ) and ('밀' not in detect ):
                    detect.append('밀')

        f.close()
        return detect

formClass = uic.loadUiType("./test.ui")[0]

class Ui(QMainWindow, formClass): 

    # def __init__(self):
    #     super().__init__()
    #     self.uid = None
    #     self.setupUi(self)
    #     self.logincam = Logincam(self)
    #     self.capcam = Capcam(self)
    #     self.logincam.start()
    def __init__(self):
        super().__init__()
        self.uid = None
        self.setupUi(self)
        self.logincam = Logincam(self)
        self.capcam = Capcam(self)
        self.initspace()

    def initspace(self):
        self.stackedWidget.setCurrentIndex(6)
        self.qPixmapFileVar = QPixmap()
        self.qPixmapFileVar.load("img865")
        self.qPixmapFileVar = self.qPixmapFileVar.scaledToWidth(600)
        self.label_15.setPixmap(self.qPixmapFileVar)
        self.pushButton_13.clicked.connect(self.projectstart)

    def projectstart(self):
        self.stackedWidget.setCurrentIndex(0)
        self.logincam.start()
    




if __name__ == '__main__':
    
    
    app = QApplication(sys.argv)
    currentUi = Ui()
    currentUi.showMaximized()
    #currentUi.show()
    
    
    
    
    sys.exit(app.exec_())

