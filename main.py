import json, time, requests
import cv2 as cv
import numpy as np
from pydantic import BaseModel


class RegionMarking(BaseModel):
    region: int
    position: list


default_window_name = "Region Marking"
label = ["Normal", "Marking", "Collecting dataset"]
mark_action = False

img = ''
img_cnt = 0
region_cnt = 0
region_save = []
x_start, y_start, x_end, y_end = 0, 0, 0, 0


def mouse_marking(envent, x, y, flags, param):
    global mark_action
    global region_cnt
    global region_cnt
    global x_start, y_start, x_end, y_end

    if envent == cv.EVENT_LBUTTONDOWN:
        x_start, y_start, x_end, y_end = x, y, x, y
        mark_action = True
    
    elif envent == cv.EVENT_MOUSEMOVE:
        if mark_action:
            x_end, y_end = x, y
    
    elif envent == cv.EVENT_LBUTTONUP:
        x_end, y_end = x, y
        mark_action = False

        region_cnt += 1
        region_save.append(RegionMarking(region= region_cnt, position= [ x_start, y_start, x_end, y_end]).model_dump())


def save_region_file():
    global region_save

    name_of_file = "region.json"
    with open(name_of_file, 'w') as file:
        json.dump(region_save, file, indent= 4)


def laod_region_file(file_name: str):
    global region_save
    global region_cnt

    try:
        with open(f"./{file_name}.json") as file:
            region_save = json.load(file)
            region_cnt = int(len(region_save))
            print(region_save)
            print(f"Load file succesfuly of {len(region_save)} region")
    except Exception as err:
        print(err) 


def main(source: str, interval: int):
    global mark_action
    global region_cnt
    global region_cnt
    global x_start, y_start, x_end, y_end

    counter = 0
    mode = 0
    last_time = 0
    start_time = time.time()

    defauilt_source = f"http://{source}/ISAPI/Streaming/channels/101/picture"
    cv.namedWindow(default_window_name)
    while True:
        named_tuple = time.localtime()
        time_string = time.strftime("%m%d%Y", named_tuple)

        response = requests.get(defauilt_source, auth=('admin', 'Hik@123.!'), stream=True).raw
        img_raw = np.asarray(bytearray(response.read()), dtype='uint8')
        img_raw = cv.imdecode(img_raw, cv.IMREAD_COLOR)

        # img_raw = cv.imread("./dataset/dummy.jpeg")
        img_scale = cv.resize(img_raw, (960, 540), interpolation=cv.INTER_AREA)
        img = img_scale.copy()

        cv.putText(img_scale, f"Mode: {label[mode]}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv.LINE_AA)
        
        if mode == 1: # Marking region
            cv.setMouseCallback(default_window_name, mouse_marking)
        
        elif mode == 2: # Collect dataset
            # cv.putText(img_scale, f"Mode: {label[mode]}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv.LINE_AA)
            if last_time > interval:
                for region in region_save:
                    counter += 1
                    img_crop = img[region["position"][1]:region["position"][3], region["position"][0]:region["position"][2]]
                    cv.imwrite(f"./dataset/IMG{counter}_{source}_{time_string}.jpeg", img_crop)
                    time.sleep(0.1)

                start_time = time.time()
        
        elif mode == 0: # Normal mode
            mark_action = False
            x_start, y_start, x_end, y_end = 0, 0, 0, 0
            cv.setMouseCallback(default_window_name, lambda *args: None)

        if len(region_save) > 0:
            for i in range(len(region_save)):
                # cv.putText(img_scale, f"{region_save[i]["region"]}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv.LINE_AA)
                cv.rectangle(img_scale, (region_save[i]["position"][0], region_save[i]["position"][1]), (region_save[i]["position"][2], region_save[i]["position"][3]), (0, 0, 255), 1)

        if mark_action:
            cv.rectangle(img_scale, (x_start, y_start), (x_end, y_end), (0, 0, 255), 1)

        end_time = time.time()
        last_time = end_time - start_time
            
        cv.imshow(default_window_name, img_scale)
        key = cv.waitKey(50)
        if key == ord('q'): # Quit windows
            break

        elif key == ord('m'): # Marking region
            mode = 1
        
        elif key == ord('r'): # Running auto collect dataset by marking region
            mode = 2

        elif key == ord('x'): # Normal mode
            mode = 0
        
        elif key == ord('d'): # Delet marking region
            if region_cnt > 0 and mode == 1:
                region_cnt -= 1
                region_save.pop()
        
        elif key == ord('l'):
            print("Must json file..!")
            file_name = input("Region file nama: ")
            laod_region_file(file_name)
        
        elif key == ord('s'): # Save marking region
            save_region_file()
    
    cv.destroyAllWindows()

if __name__ == "__main__":
    source = input("IP Camera: ")
    interval = input("Interval Collection: ")

    main(source, int(interval))
    print("OK")