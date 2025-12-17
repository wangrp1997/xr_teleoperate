import os, sys
this_file = os.path.abspath(__file__)
project_root = os.path.abspath(os.path.join(os.path.dirname(this_file), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import json
import numpy as np
import zmq
from televuer import TeleVuerWrapper
import logging_mp
logger_mp = logging_mp.get_logger(__name__, level=logging_mp.INFO)


def matrix_to_list(matrix):
    """将 numpy 4x4 矩阵转换为 Python list"""
    if matrix is None:
        return None
    return matrix.tolist()


def array_to_list(arr):
    """将 numpy array 转换为 Python list"""
    if arr is None:
        return None
    return arr.tolist()


def run_xr_data_forwarder():
    """
    XR 数据转发服务
    - 从 Quest3 采集所有原始 XR 数据
    - 通过 ZeroMQ PUB socket 发送 JSON 格式数据
    - 不做任何阈值/映射处理，只转发原始数据
    """
    use_hand_track = False
    
    # ZeroMQ 配置
    zmq_port = 5555  # 可以改成你想要的端口
    zmq_topic = "xr_raw_data"  # 可选：ZeroMQ topic filter
    
    # 初始化 ZeroMQ PUB socket
    zmq_context = zmq.Context()
    zmq_publisher = zmq_context.socket(zmq.PUB)
    zmq_publisher.bind(f"tcp://*:{zmq_port}")
    logger_mp.info(f"[ZeroMQ] Publisher started on tcp://*:{zmq_port}, topic: {zmq_topic}")
    
    # teleimager 配置（如果需要图像流）
    try:
        from teleimager.image_client import ImageClient
        img_client = ImageClient(host="192.168.123.164")
        camera_config = img_client.get_cam_config()
        use_teleimager = True
    except Exception as e:
        logger_mp.warning(f"[ImageClient] Failed to connect to teleimager: {e}, using pure televuer mode")
        camera_config = {
            'head_camera': {
                'binocular': True,
                'image_shape': (480, 1280),
                'fps': 30.0,
                'enable_zmq': False,
                'enable_webrtc': False,
                'webrtc_port': 60001
            }
        }
        use_teleimager = False
    
    # 初始化 TeleVuerWrapper
    if use_teleimager:
        tv_wrapper = TeleVuerWrapper(
            use_hand_tracking=use_hand_track,
            binocular=camera_config['head_camera']['binocular'],
            img_shape=camera_config['head_camera']['image_shape'],
            display_mode="immersive",
            display_fps=camera_config['head_camera']['fps'],
            zmq=camera_config['head_camera']['enable_zmq'],
            webrtc=camera_config['head_camera']['enable_webrtc'],
            webrtc_url=f"https://192.168.123.164:{camera_config['head_camera']['webrtc_port']}/offer" if camera_config['head_camera']['enable_webrtc'] else None
        )
    else:
        # pure televuer 模式（不需要 teleimager）
        tv_wrapper = TeleVuerWrapper(
            use_hand_tracking=use_hand_track,
            binocular=True,
            img_shape=(480, 1280),
            display_fps=30.0,
            display_mode="pass-through",  # 不需要图像流时用 pass-through
            zmq=False,
            webrtc=False,
            webrtc_url=None
        )
    
    try:
        input("Press Enter to start XR data forwarder...")
        running = True
        frame_count = 0
        
        while running:
            start_time = time.time()
            
            # 获取图像（如果需要，且不是 pass-through 模式）
            if use_teleimager and camera_config['head_camera'].get('enable_zmq', False):
                try:
                    img, _ = img_client.get_head_frame()
                    if img is not None:
                        tv_wrapper.render_to_xr(img)
                except Exception as e:
                    logger_mp.warning(f"[ImageClient] Failed to get frame: {e}")
            
            # 获取 XR 数据
            teleData = tv_wrapper.get_tele_data()
            
            # 构建 JSON 数据包（包含所有原始数据）
            data_packet = {
                "timestamp": time.time(),
                "frame_id": frame_count,
                "use_hand_tracking": use_hand_track,
                
                # 位姿数据（4x4 矩阵）
                "head_pose": matrix_to_list(teleData.head_pose),
                "left_wrist_pose": matrix_to_list(teleData.left_wrist_pose),
                "right_wrist_pose": matrix_to_list(teleData.right_wrist_pose),
            }
            
            # 根据模式添加不同的数据（只包含 test_tv_wrapper.py 实际使用的字段）
            if use_hand_track:
                # 手势跟踪模式（参考 test_tv_wrapper.py 的字段）
                hand_data = {
                    "left_hand_pos": array_to_list(teleData.left_hand_pos) if teleData.left_hand_pos is not None else None,
                    "right_hand_pos": array_to_list(teleData.right_hand_pos) if teleData.right_hand_pos is not None else None,
                }
                
                # 检查旋转数据是否存在（参考 test_tv_wrapper.py 的处理方式）
                if teleData.left_hand_rot is not None:
                    hand_data["left_hand_rot"] = array_to_list(teleData.left_hand_rot)
                else:
                    hand_data["left_hand_rot"] = None
                    
                if teleData.right_hand_rot is not None:
                    hand_data["right_hand_rot"] = array_to_list(teleData.right_hand_rot)
                else:
                    hand_data["right_hand_rot"] = None
                
                # 只包含 test_tv_wrapper.py 实际打印的 Value 字段（不包含 bool 字段，保持原始数据类型）
                hand_data.update({
                    "left_hand_pinchValue": teleData.left_hand_pinchValue,
                    "left_hand_squeezeValue": teleData.left_hand_squeezeValue,
                    "right_hand_pinchValue": teleData.right_hand_pinchValue,
                    "right_hand_squeezeValue": teleData.right_hand_squeezeValue,
                })
                
                data_packet.update(hand_data)
            else:
                # 控制器模式（只包含 test_tv_wrapper.py 实际打印的字段，保持原始数据类型）
                data_packet.update({
                    # 左手控制器
                    "left_ctrl_triggerValue": teleData.left_ctrl_triggerValue,
                    "left_ctrl_squeezeValue": teleData.left_ctrl_squeezeValue,
                    "left_ctrl_thumbstickValue": array_to_list(teleData.left_ctrl_thumbstickValue),
                    "left_ctrl_xButton": teleData.left_ctrl_aButton,  # 字段名改成了 xButton，但值保持原始 bool
                    "left_ctrl_yButton": teleData.left_ctrl_bButton,  # 字段名改成了 yButton，但值保持原始 bool
                    
                    # 右手控制器
                    "right_ctrl_triggerValue": teleData.right_ctrl_triggerValue,
                    "right_ctrl_squeezeValue": teleData.right_ctrl_squeezeValue,
                    "right_ctrl_thumbstickValue": array_to_list(teleData.right_ctrl_thumbstickValue),
                    "right_ctrl_aButton": teleData.right_ctrl_aButton,
                    "right_ctrl_bButton": teleData.right_ctrl_bButton,
                })
            
            # 序列化为 JSON 并发送
            try:
                json_str = json.dumps(data_packet)
                # ZeroMQ PUB 模式：先发送 topic（可选），再发送数据
                zmq_publisher.send_string(f"{zmq_topic} {json_str}")
                
                # 每 30 帧打印一次日志（避免刷屏）
                if frame_count % 30 == 0:
                    logger_mp.info(f"[Forwarder] Frame {frame_count}: Sent data packet (size: {len(json_str)} bytes)")
                    logger_mp.debug(f"[Forwarder] Sample data: left_ctrl_triggerValue={data_packet.get('left_ctrl_triggerValue', 'N/A')}, "
                                  f"right_ctrl_triggerValue={data_packet.get('right_ctrl_triggerValue', 'N/A')}")
            except Exception as e:
                logger_mp.error(f"[Forwarder] Failed to send data: {e}")
            
            frame_count += 1
            
            # 控制循环频率
            current_time = time.time()
            time_elapsed = current_time - start_time
            sleep_time = max(0, 0.016 - time_elapsed)  # ~60 FPS
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        running = False
        logger_mp.warning("KeyboardInterrupt, exiting program...")
    except Exception as e:
        logger_mp.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # 清理资源
        tv_wrapper.close()
        zmq_publisher.close()
        zmq_context.term()
        logger_mp.warning("Finally, exiting program...")


if __name__ == '__main__':
    run_xr_data_forwarder()

