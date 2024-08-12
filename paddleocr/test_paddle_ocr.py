import os
import cv2
from paddleocr import PPStructure,draw_structure_result,save_structure_res

table_engine = PPStructure(show_log=True, use_gpu=False)

save_folder = './output'
img_path = '/home/aaron/Anuk_Test_CORS_Pics/Chris_Bilanzvergleich_2013-2017-1.jpg'
img = cv2.imread(img_path)
result = table_engine(img)
save_structure_res(result, save_folder,os.path.basename(img_path).split('.')[0])

for line in result:
    line.pop('img')
    print(line)

from PIL import Image

image = Image.open(img_path).convert('RGB')
im_show = draw_structure_result(image, result,)
im_show = Image.fromarray(im_show)
im_show.save('result.jpg')
