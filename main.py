# ---------------------------------------
# K210 (MaixPy) Face Recognition
# + Feature-level SHA-256 Hash Protection
# SD root contains: /sd/KPU and /sd/k210 (school provided)
# ---------------------------------------

import sensor, image, lcd, time, gc
import struct, hashlib
import uos

from maix import KPU

# -----------------------------
# Helper: check if file exists
# -----------------------------
def file_exists(path):
    try:
        f = open(path, "rb")
        f.close()
        return True
    except:
        return False

def find_model(candidates):
    """
    Return first existing model path from candidates.
    If not found, try searching in /sd/KPU and /sd/k210 by filename.
    """
    # 1) Try full candidate paths
    for p in candidates:
        if file_exists(p):
            return p

    # 2) Try search by filename in known base dirs
    base_dirs = ["/sd/KPU", "/sd/k210"]
    for p in candidates:
        fname = p.split("/")[-1]
        for bd in base_dirs:
            try:
                items = uos.listdir(bd)
                if fname in items:
                    return bd + "/" + fname
            except:
                pass

    return None

# -----------------------------
# Init LCD + Camera
# -----------------------------
lcd.init()

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)  # 320x240
sensor.skip_frames(time=200)
clock = time.clock()

# -----------------------------
# Load Models (AUTO-DETECT PATHS)
# -----------------------------
# YOLO anchors (commonly used in K210 face detect demos)
anchor = (
    0.1075, 0.126875, 0.126875, 0.175, 0.1465625, 0.2246875,
    0.1953125, 0.25375, 0.2440625, 0.351875, 0.341875, 0.4721875,
    0.5078125, 0.6696875, 0.8984375, 1.099687, 2.129062, 2.425937
)

# --- Model file candidates (you can add more names if your school uses different names) ---
FACE_DET_CANDIDATES = [
    "/sd/KPU/yolo_face_detect/face_detect_320x240.kmodel",
    "/sd/k210/yolo_face_detect/face_detect_320x240.kmodel",
    "/sd/KPU/face_detect_320x240.kmodel",
    "/sd/k210/face_detect_320x240.kmodel",
    "/sd/KPU/face_detect.kmodel",
    "/sd/k210/face_detect.kmodel",
]

LD5_CANDIDATES = [
    "/sd/KPU/face_recognization/ld5.kmodel",
    "/sd/k210/face_recognization/ld5.kmodel",
    "/sd/KPU/ld5.kmodel",
    "/sd/k210/ld5.kmodel",
]

FEA_CANDIDATES = [
    "/sd/KPU/face_recognization/feature_extraction.kmodel",
    "/sd/k210/face_recognization/feature_extraction.kmodel",
    "/sd/KPU/feature_extraction.kmodel",
    "/sd/k210/feature_extraction.kmodel",
]

face_det_model = find_model(FACE_DET_CANDIDATES)
ld5_model      = find_model(LD5_CANDIDATES)
fea_model      = find_model(FEA_CANDIDATES)

if (face_det_model is None) or (ld5_model is None) or (fea_model is None):
    lcd.clear()
    img = image.Image(size=(320, 240))
    img.draw_string(10, 10, "MODEL NOT FOUND!", scale=2, color=(255, 0, 0))
    img.draw_string(10, 40, "Check /sd/KPU or /sd/k210", scale=2, color=(255, 255, 0))
    img.draw_string(10, 70, "Need: face_detect, ld5, feature_extraction", scale=1, color=(255, 255, 255))
    lcd.display(img)
    while True:
        time.sleep_ms(1000)

print("[OK] face_det_model:", face_det_model)
print("[OK] ld5_model     :", ld5_model)
print("[OK] fea_model     :", fea_model)

# Load YOLO face detection
kpu = KPU()
kpu.load_kmodel(face_det_model)
kpu.init_yolo2(anchor, anchor_num=9, img_w=320, img_h=240, net_w=320, net_h=240,
               layer_w=10, layer_h=8, threshold=0.7, nms_value=0.2, classes=1)

# Load 5-point landmark model
ld5_kpu = KPU()
ld5_kpu.load_kmodel(ld5_model)

# Load feature extraction model
fea_kpu = KPU()
fea_kpu.load_kmodel(fea_model)

# -----------------------------
# Face alignment config (64x64)
# -----------------------------
FACE_PIC_SIZE = 64
dst_point = [
    (int(38.2946 * FACE_PIC_SIZE / 112), int(51.6963 * FACE_PIC_SIZE / 112)),
    (int(73.5318 * FACE_PIC_SIZE / 112), int(51.5014 * FACE_PIC_SIZE / 112)),
    (int(56.0252 * FACE_PIC_SIZE / 112), int(71.7366 * FACE_PIC_SIZE / 112)),
    (int(41.5493 * FACE_PIC_SIZE / 112), int(92.3655 * FACE_PIC_SIZE / 112)),
    (int(70.7299 * FACE_PIC_SIZE / 112), int(92.2041 * FACE_PIC_SIZE / 112)),
]
feature_img = image.Image(size=(64, 64), copy_to_fb=False)
feature_img.pix_to_ai()

# -----------------------------
# Privacy protection: feature -> SHA256
# -----------------------------
def feature_to_sha256(feature):
    # Convert feature (32 floats) to bytes, then SHA-256 (irreversible)
    flist = list(feature.to_list())                # should be 32 floats
    # If your model outputs not 32 floats, this will throw; then you must adjust "<32f"
    fbytes = struct.pack("<32f", *flist)
    return hashlib.sha256(fbytes).hexdigest()

# -----------------------------
# Recognition storage (raw features for comparison)
# NOTE: For recognition, we keep raw features in RAM, but DO NOT print them.
# -----------------------------
record_ftrs = []
THRESHOLD = 80.5

def extend_box(x, y, w, h, scale=0):
    x1_t = x - scale * w
    x2_t = x + w + scale * w
    y1_t = y - scale * h
    y2_t = y + h + scale * h
    x1 = int(x1_t) if x1_t > 1 else 1
    x2 = int(x2_t) if x2_t < 320 else 319
    y1 = int(y1_t) if y1_t > 1 else 1
    y2 = int(y2_t) if y2_t < 240 else 239
    return x1, y1, x2 - x1 + 1, y2 - y1 + 1

# -----------------------------
# (Optional) Register control: use BOOT_KEY if available
# If this part errors on your firmware, tell me and I give you "always register first 3 faces" mode.
# -----------------------------
start_processing = False
try:
    from maix import GPIO
    from fpioa_manager import fm
    from board import board_info

    BOUNCE_MS = 60
    fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0)
    key_gpio = GPIO(GPIO.GPIOHS0, GPIO.IN)

    def set_key_state(*_):
        global start_processing
        start_processing = True
        time.sleep_ms(BOUNCE_MS)

    key_gpio.irq(set_key_state, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT)
    boot_key_ok = True
except:
    boot_key_ok = False

# -----------------------------
# Main loop
# -----------------------------
try:
    while True:
        gc.collect()
        clock.tick()
        img = sensor.snapshot()

        kpu.run_with_output(img)
        dect = kpu.regionlayer_yolo2()

        if dect:
            for l in dect:
                # Crop face area
                x1, y1, cut_w, cut_h = extend_box(l[0], l[1], l[2], l[3], scale=0)
                face_cut = img.cut(x1, y1, cut_w, cut_h)
                face_cut_128 = face_cut.resize(128, 128)
                face_cut_128.pix_to_ai()

                # 5 landmarks
                out = ld5_kpu.run_with_output(face_cut_128, getlist=True)
                face_key_point = []
                for j in range(5):
                    px = int(KPU.sigmoid(out[2 * j]) * cut_w + x1)
                    py = int(KPU.sigmoid(out[2 * j + 1]) * cut_h + y1)
                    face_key_point.append((px, py))

                # Align face -> feature_img (64x64)
                T = image.get_affine_transform(face_key_point, dst_point)
                image.warp_affine_ai(img, feature_img, T)

                # Extract feature vector (32-d float)
                feature = fea_kpu.run_with_output(feature_img, get_feature=True)

                # ---- Feature-level SHA-256 hash (privacy evidence) ----
                try:
                    feature_hash = feature_to_sha256(feature)
                except:
                    feature_hash = "SHA256_ERROR"

                # Show a short hash prefix on LCD (do NOT show raw feature)
                img.draw_string(0, 200, "H:" + feature_hash[:12], color=(255, 255, 0), scale=2)

                # ---- Recognition compare ----
                index = -1
                max_score = 0.0
                if record_ftrs:
                    scores = []
                    for rf in record_ftrs:
                        scores.append(kpu.feature_compare(rf, feature))
                    max_score = max(scores)
                    index = scores.index(max_score)

                # Draw box
                img.draw_rectangle(l[0], l[1], l[2], l[3], color=(0, 255, 0))

                # Decide recognized or not
                if record_ftrs and (max_score > THRESHOLD):
                    img.draw_string(0, 170, "ID:%d  %2.1f" % (index, max_score),
                                    color=(0, 255, 0), scale=2)
                else:
                    img.draw_string(0, 170, "Unknown", color=(255, 0, 0), scale=2)

                # ---- Registration (press BOOT_KEY) ----
                if boot_key_ok and start_processing:
                    record_ftrs.append(feature)  # store raw feature for comparison ONLY
                    uid = len(record_ftrs) - 1
                    print("Registered User:", uid)
                    print("PRIVACY_HASH_SHA256:", feature_hash)  # evidence for report
                    start_processing = False

                # cleanup
                del face_key_point
                del face_cut_128
                del face_cut

                # Only process first face for stability (optional)
                break

        # FPS + hint
        img.draw_string(0, 0, "%2.1ffps" % clock.fps(), color=(0, 60, 255), scale=2)
        if boot_key_ok:
            img.draw_string(0, 220, "BOOT_KEY: register", color=(255, 100, 0), scale=2)
        else:
            img.draw_string(0, 220, "BOOT_KEY not enabled", color=(255, 100, 0), scale=2)

        lcd.display(img)

finally:
    kpu.deinit()
    ld5_kpu.deinit()
    fea_kpu.deinit()
