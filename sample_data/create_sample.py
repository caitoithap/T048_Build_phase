import os
import cv2
import numpy as np
from pathlib import Path

def generate_sample_dataset(output_dir="sample_data", num_frames=10):
    """
    Generates synthetic frames with moving shapes (cars/pedestrians) to test tracking and pre-labeling.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    img_w, img_h = 1280, 720
    print(f"🖼 Generating {num_frames} synthetic test frames in [{out_path}]...")

    for f_idx in range(num_frames):
        # Dark asphalt background
        frame = np.full((img_h, img_w, 3), 40, dtype=np.uint8)
        
        # Draw road lane markings (white & yellow lines)
        cv2.line(frame, (0, 600), (1280, 600), (255, 255, 255), 4)
        cv2.line(frame, (0, 400), (1280, 400), (0, 255, 255), 3)

        # Vehicle 1: Red sedan moving right
        car1_x = 100 + f_idx * 40
        car1_y = 450
        cv2.rectangle(frame, (car1_x, car1_y), (car1_x + 180, car1_y + 80), (0, 0, 220), -1)
        cv2.rectangle(frame, (car1_x + 30, car1_y - 35), (car1_x + 140, car1_y), (0, 0, 180), -1)
        # Wheels
        cv2.circle(frame, (car1_x + 35, car1_y + 80), 18, (10, 10, 10), -1)
        cv2.circle(frame, (car1_x + 145, car1_y + 80), 18, (10, 10, 10), -1)
        cv2.putText(frame, "CAR 1", (car1_x + 40, car1_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Vehicle 2: Blue SUV moving left
        car2_x = 900 - f_idx * 35
        car2_y = 250
        cv2.rectangle(frame, (car2_x, car2_y), (car2_x + 200, car2_y + 100), (220, 100, 0), -1)
        cv2.putText(frame, "SUV 2", (car2_x + 60, car2_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Frame counter text
        cv2.putText(frame, f"AI20K CPU Test Frame: {f_idx+1}/{num_frames}", (30, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        file_name = out_path / f"frame_{f_idx:06d}.jpg"
        cv2.imwrite(str(file_name), frame)

    print(f"✅ Created {num_frames} sample test images successfully!")
    return str(out_path)

if __name__ == "__main__":
    generate_sample_dataset()
