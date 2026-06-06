# -*- coding: cp1254 -*-

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# =========================
# 1. KLASÖR OLUŞTURMA
# =========================

os.makedirs("report_images", exist_ok=True)

# =========================
# 2. DİYAGRAM ADIMLARI
# =========================

steps = [
    "Video Girisi",
    "Frame Okuma",
    "YOLO ile Arac Tespiti",
    "Arac Siniflarini Filtreleme",
    "Siyah-Beyaz Maske Olusturma",
    "Arac Sayimi",
    "Trafik Yogunlugu Analizi",
    "Karar Destek Sistemi",
    "Ciktilar\n(Video + Maske + CSV + Grafik)"
]

# =========================
# 3. ŞEKİL OLUŞTURMA
# =========================

fig, ax = plt.subplots(figsize=(8, 13))

ax.set_xlim(0, 10)
ax.set_ylim(0, 16)
ax.axis("off")

# =========================
# 4. BAŞLIK
# =========================

ax.text(
    5,
    15.3,
    "Video Segmentasyonu Tabanli Trafik Yogunlugu Karar Destek Sistemi",
    ha="center",
    va="center",
    fontsize=15,
    fontweight="bold"
)

# =========================
# 5. KUTULAR VE OKLAR
# =========================

y = 14

for i, step in enumerate(steps):
    box = FancyBboxPatch(
        (2.2, y - 0.45),
        5.6,
        0.9,
        boxstyle="round,pad=0.08,rounding_size=0.15",
        linewidth=1.5,
        edgecolor="black",
        facecolor="white"
    )

    ax.add_patch(box)

    ax.text(
        5,
        y,
        step,
        ha="center",
        va="center",
        fontsize=12
    )

    if i < len(steps) - 1:
        ax.annotate(
            "",
            xy=(5, y - 1.0),
            xytext=(5, y - 0.5),
            arrowprops=dict(
                arrowstyle="->",
                linewidth=1.5
            )
        )

    y -= 1.5

# =========================
# 6. KAYDETME
# =========================

output_path = "report_images/system_flow_diagram.png"

plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close()

print("Sistem akis diyagrami olusturuldu:", output_path)