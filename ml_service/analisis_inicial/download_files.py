import gdown
import os

download_folder = "C:/Users/jhons/Desktop/Alerta vial/alerta-via/ml_service/analisis_inicial"  

files = {
    "hurtos_a_persona": "1VUXpxhpssv7pfZ1lupc0FMxBt2Pnvsp5",
    "dataset_postprocess": "1u9feMj0Kdts3jBhvCbYNgHGUHLFQArrd"
}

for name, file_id in files.items():
    file_path = os.path.join(download_folder, f"{name}.csv")
    gdown.download(f"https://drive.google.com/uc?id={file_id}", file_path, quiet=False)

