import cv2
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO


# 1. PROJE KLASÖRLERİ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

data_dir = os.path.join(BASE_DIR, "data")
output_dir = os.path.join(BASE_DIR, "outputs")
report_dir = os.path.join(BASE_DIR, "report_images")

os.makedirs(output_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)

video_path = os.path.join(data_dir, "traffic_video.mp4")

detection_video_path = os.path.join(output_dir, "arac_tespit_sonucu.avi")
mask_video_path = os.path.join(output_dir, "segmentasyon_maskesi.avi")
csv_path = os.path.join(output_dir, "analiz_sonuclari.csv")
graph_path = os.path.join(report_dir, "arac_yogunluk_grafigi.png")

print("Video yolu:", video_path)


# 2. YOLO MODELİ
model = YOLO("yolov8n.pt")

# COCO sınıf ID'leri:
# 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
vehicle_classes = [2, 3, 5, 7]

# 3. VİDEO AÇMA
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    raise RuntimeError("Video açılamadı. data klasöründeki video adını kontrol et.")

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print("FPS:", fps)
print("Frame sayısı:", frame_count)
print("Video boyutu:", original_width, "x", original_height)


# 4. ÇIKTI VİDEOLARI
fourcc = cv2.VideoWriter_fourcc(*"XVID")

detection_out = cv2.VideoWriter(
    detection_video_path,
    fourcc,
    fps,
    (original_width, original_height)
)

mask_out = cv2.VideoWriter(
    mask_video_path,
    fourcc,
    fps,
    (original_width, original_height)
)


# 5. ANALİZ LİSTELERİ
frame_numbers = []
vehicle_counts = []
density_labels = []

frame_no = 0

# 5.1 KARŞILAŞTIRMA İÇİN ÖRNEK FRAME KAYITLARI
saved_examples = {
    "Dusuk Yogunluk": False,
    "Orta Yogunluk": False,
    "Yuksek Yogunluk": False
}

example_file_names = {
    "Dusuk Yogunluk": "low_density",
    "Orta Yogunluk": "medium_density",
    "Yuksek Yogunluk": "high_density"
}


process_every_n_frame = 3

last_boxes = []
last_vehicle_count = 0
last_density = "Bekleniyor"
last_decision_color = (255, 255, 255)


# 6. VİDEO İŞLEME DÖNGÜSÜ
while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_no += 1

    detection_frame = frame.copy()

    # Siyah-beyaz maske
    # Siyah = arka plan
    # Beyaz = araç bölgeleri
    mask = np.zeros((original_height, original_width), dtype=np.uint8)

    
    # 7. YOLO ARAÇ TESPİTİ
    if frame_no % process_every_n_frame == 0:
        results = model(frame, conf=0.35, verbose=False)

        current_boxes = []
        vehicle_count = 0

        for result in results:
            boxes = result.boxes

            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                if cls_id in vehicle_classes:
                    vehicle_count += 1

                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    class_name = model.names[cls_id]

                    current_boxes.append((x1, y1, x2, y2, class_name, conf))

      
        # 8. KARAR DESTEK SİSTEMİ
        if vehicle_count <= 5:
            density = "Dusuk Yogunluk"
            decision_color = (0, 255, 0)
        elif vehicle_count <= 12:
            density = "Orta Yogunluk"
            decision_color = (0, 255, 255)
        else:
            density = "Yuksek Yogunluk"
            decision_color = (0, 0, 255)

        last_boxes = current_boxes
        last_vehicle_count = vehicle_count
        last_density = density
        last_decision_color = decision_color

    vehicle_count = last_vehicle_count
    density = last_density
    decision_color = last_decision_color

   
    # 9. KUTULAR VE MASKE
    for box_data in last_boxes:
        x1, y1, x2, y2, class_name, conf = box_data

        # Araç tespit ekranı
        cv2.rectangle(
            detection_frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        cv2.putText(
            detection_frame,
            f"{class_name} {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # Maske ekranı
        cv2.rectangle(
            mask,
            (x1, y1),
            (x2, y2),
            255,
            -1
        )

   
    # 10. ARAÇ TESPİT EKRANI BİLGİ PANELİ
    cv2.rectangle(detection_frame, (20, 20), (650, 140), (0, 0, 0), -1)

    cv2.putText(
        detection_frame,
        f"Frame: {frame_no}",
        (40, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    cv2.putText(
        detection_frame,
        f"Toplam Arac Sayisi: {vehicle_count}",
        (40, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    cv2.putText(
        detection_frame,
        f"Karar: {density}",
        (40, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        decision_color,
        2
    )

  
    # 11. MASKE EKRANI BİLGİ PANELİ
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    cv2.rectangle(mask_bgr, (20, 20), (650, 100), (0, 0, 0), -1)

    cv2.putText(
        mask_bgr,
        "Siyah-Beyaz Segmentasyon Maskesi",
        (40, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    cv2.putText(
        mask_bgr,
        "Beyaz: Arac | Siyah: Arka Plan",
        (40, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # 12. ÇIKTI VİDEOLARINA YAZ
    detection_out.write(detection_frame)
    mask_out.write(mask_bgr)

 
    # 12.1 KARŞILAŞTIRMA İÇİN ÖRNEK FRAME KAYDETME
    if density in saved_examples and saved_examples[density] == False:
        file_prefix = example_file_names[density]

        detection_image_path = os.path.join(
            report_dir,
            f"{file_prefix}_detection.png"
        )

        mask_image_path = os.path.join(
            report_dir,
            f"{file_prefix}_mask.png"
        )

        cv2.imwrite(detection_image_path, detection_frame)
        cv2.imwrite(mask_image_path, mask_bgr)

        saved_examples[density] = True

        print(f"Örnek çıktı kaydedildi: {density}")

    
    # 13. EKRANDA AYRI AYRI GÖSTER
    display_detection = cv2.resize(detection_frame, (960, 540))
    display_mask = cv2.resize(mask_bgr, (960, 540))

    cv2.imshow("Arac Tespiti ve Karar Destek Sistemi", display_detection)
    cv2.imshow("Siyah-Beyaz Segmentasyon Maskesi", display_mask)

   
    # 14. ANALİZ VERİSİ KAYDET
    frame_numbers.append(frame_no)
    vehicle_counts.append(vehicle_count)
    density_labels.append(density)

   
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# 15. KAYNAKLARI KAPAT
cap.release()
detection_out.release()
mask_out.release()
cv2.destroyAllWindows()

# 16. CSV KAYDETME
df = pd.DataFrame({
    "Frame": frame_numbers,
    "Vehicle_Count": vehicle_counts,
    "Density_Decision": density_labels
})

df.to_csv(csv_path, index=False)


# 17. GRAFİK KAYDETME
plt.figure(figsize=(12, 6))
plt.plot(frame_numbers, vehicle_counts)
plt.xlabel("Frame Numarası")
plt.ylabel("Araç Sayısı")
plt.title("Frame Bazlı Trafik Yoğunluğu")
plt.grid(True)
plt.savefig(graph_path, dpi=300)
plt.close()

# 18. ANALYSIS SUMMARY KAYDETME
average_count = np.mean(vehicle_counts)
max_count = np.max(vehicle_counts)
min_count = np.min(vehicle_counts)

summary_path = os.path.join(output_dir, "analysis_summary.txt")

density_distribution = df["Density_Decision"].value_counts()

with open(summary_path, "w", encoding="utf-8") as file:
    file.write("VIDEO SEGMENTASYONU ANALIZ OZETI\n")
    file.write("================================\n\n")

    file.write("Video Dosyasi:\n")
    file.write(f"{video_path}\n\n")

    file.write("Video Bilgileri:\n")
    file.write(f"FPS: {fps}\n")
    file.write(f"Frame Sayisi: {frame_count}\n")
    file.write(f"Video Boyutu: {original_width} x {original_height}\n\n")

    file.write("Ozet Bulgular:\n")
    file.write(f"Ortalama Arac Sayisi: {round(average_count, 2)}\n")
    file.write(f"Maksimum Arac Sayisi: {max_count}\n")
    file.write(f"Minimum Arac Sayisi: {min_count}\n\n")

    file.write("Yogunluk Karar Dagilimi:\n")
    file.write(str(density_distribution))
    file.write("\n\n")

    file.write("Olusturulan Dosyalar:\n")
    file.write(f"Arac Tespit Videosu: {detection_video_path}\n")
    file.write(f"Segmentasyon Maskesi Videosu: {mask_video_path}\n")
    file.write(f"CSV Dosyasi: {csv_path}\n")
    file.write(f"Grafik: {graph_path}\n\n")

    file.write("Karsilastirma Icin Kaydedilen Ornek Gorseller:\n")
    for density_name, is_saved in saved_examples.items():
        if is_saved:
            file_prefix = example_file_names[density_name]
            file.write(f"{density_name}: {file_prefix}_detection.png ve {file_prefix}_mask.png\n")
        else:
            file.write(f"{density_name}: Bu yogunluk seviyesine ait uygun frame bulunamadi.\n")


# 19. ÖZET SONUÇLAR
print("\nAnaliz tamamlandı.")

print("\nOluşturulan dosyalar:")
print("Araç tespit videosu:", detection_video_path)
print("Segmentasyon maskesi videosu:", mask_video_path)
print("CSV dosyası:", csv_path)
print("Grafik:", graph_path)
print("Analiz özeti:", summary_path)

print("\nKarşılaştırma için kaydedilen örnek görseller:")
for density_name, is_saved in saved_examples.items():
    if is_saved:
        file_prefix = example_file_names[density_name]
        print(f"{density_name}: {file_prefix}_detection.png ve {file_prefix}_mask.png")
    else:
        print(f"{density_name}: uygun frame bulunamadı")

print("\nÖzet Bulgular")
print("Ortalama araç sayısı:", round(average_count, 2))
print("Maksimum araç sayısı:", max_count)
print("Minimum araç sayısı:", min_count)

print("\nYoğunluk karar dağılımı:")
print(density_distribution)