import cv2
import torch
import math
from ultralytics import YOLO
from open_video import ask_openfilename
from pathlib import Path

def calculate_midpoint(p1, p2):
    """计算两点的中点 (x, y)"""
    return (int((p1[0] + p2[0]) / 2), int((p1[1] + p2[1]) / 2))

def calculate_angle(p1, p2, p3):
    """
    计算三点构成的夹角 (p1-p2-p3)，其中 p2 是顶点。
    返回角度值（0-180度）。
    """
    # 构造两个向量：p2 -> p1 和 p2 -> p3
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    
    # 计算点积
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    
    # 计算向量模长
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
        
    # 计算余弦值并确保在 [-1, 1] 范围内（防止浮点数精度误差）
    cos_theta = dot_product / (mag1 * mag2)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    
    # 返回对应的角度
    return math.degrees(math.acos(cos_theta))

if __name__ == "__main__":
    input_video_path = ask_openfilename()
    if not input_video_path:
        print("error: no video file selected.")
        exit()

    model = YOLO("yolo26x-pose.pt") # 注意：如果你使用的是官方模型，通常是 yolov8x-pose.pt 或 yolov11x-pose.pt
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)

    cap = cv2.VideoCapture(input_video_path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 修复了路径拼接的问题，并确保 predict 文件夹存在
    out_dir = Path("predict")
    out_dir.mkdir(exist_ok=True)
    save_path = str(out_dir / Path(input_video_path).name)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

    print(f"正在处理视频... 结果将保存至: {save_path}")
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            break

        results = model(frame, verbose=False)
        annotated_frame = results[0].plot()

        if results[0].keypoints is not None:
            keypoints_all_people = results[0].keypoints.data

            for i, person_kpts in enumerate(keypoints_all_people):
                kpts = person_kpts.cpu().numpy()

                # 防止关键点数据不全
                if len(kpts) < 15:
                    continue

                # --- 修复核心：将坐标强制转换为整数元组 ---
                l_shoulder = (int(kpts[5][0]), int(kpts[5][1]))
                r_shoulder = (int(kpts[6][0]), int(kpts[6][1]))
                l_hip = (int(kpts[11][0]), int(kpts[11][1]))
                r_hip = (int(kpts[12][0]), int(kpts[12][1]))
                
                l_elbow = (int(kpts[7][0]), int(kpts[7][1]))
                r_elbow = (int(kpts[8][0]), int(kpts[8][1]))
                l_knee = (int(kpts[13][0]), int(kpts[13][1]))
                r_knee = (int(kpts[14][0]), int(kpts[14][1]))

                if l_shoulder[0] > 0 and r_shoulder[0] > 0 and l_hip[0] > 0 and r_hip[0] > 0:
                    shoulder_mid = calculate_midpoint(l_shoulder, r_shoulder)
                    hip_mid = calculate_midpoint(l_hip, r_hip)

                    # 画出脊柱
                    cv2.line(annotated_frame, shoulder_mid, hip_mid, (0, 255, 255), 3)
                    cv2.circle(annotated_frame, shoulder_mid, 5, (0, 0, 255), -1)
                    cv2.circle(annotated_frame, hip_mid, 5, (0, 0, 255), -1)

                    # 初始化角度
                    body_angle = 0.0
                    l_arm_angle = 0.0
                    r_arm_angle = 0.0

                    # 1. 计算身体角度 (脊柱 与 腿部 的夹角)
                    if l_knee[0] > 0 and r_knee[0] > 0:
                        knee_mid = calculate_midpoint(l_knee, r_knee)
                        body_angle = calculate_angle(shoulder_mid, hip_mid, knee_mid)
                        cv2.line(annotated_frame, hip_mid, knee_mid, (255, 255, 0), 2)

                    # 2. 计算左手臂角度 (左臀部 - 左肩膀 - 左手肘)
                    if l_elbow[0] > 0:
                        l_arm_angle = calculate_angle(l_hip, l_shoulder, l_elbow)
                        cv2.line(annotated_frame, l_shoulder, l_elbow, (255, 0, 255), 2)

                    # 3. 计算右手臂角度 (右臀部 - 右肩膀 - 右手肘)
                    if r_elbow[0] > 0:
                        r_arm_angle = calculate_angle(r_hip, r_shoulder, r_elbow)
                        cv2.line(annotated_frame, r_shoulder, r_elbow, (255, 0, 255), 2)

                    # --- 输出信息到视频右上角 ---
                    text_x = width - 400
                    text_y = 60 + (i * 120) 
                    
                    cv2.putText(annotated_frame, f"P{i+1} Body Angle: {int(body_angle)} deg", 
                                (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f"P{i+1} L-Arm Angle: {int(l_arm_angle)} deg", 
                                (text_x, text_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    cv2.putText(annotated_frame, f"P{i+1} R-Arm Angle: {int(r_arm_angle)} deg", 
                                (text_x, text_y + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        out.write(annotated_frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("处理完成！")