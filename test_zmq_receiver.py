#!/usr/bin/env python3
"""
ZeroMQ 接收端测试脚本
用于测试 xr_data_forwarder.py 发送的 XR 数据
"""

import zmq
import json
import time
import sys


def test_zmq_receiver(zmq_host="localhost", zmq_port=5555, zmq_topic="xr_raw_data"):
    """
    测试 ZeroMQ 数据接收（完整输出所有数据）
    
    Args:
        zmq_host: ZeroMQ 服务器地址
        zmq_port: ZeroMQ 端口
        zmq_topic: ZeroMQ topic 名称
    """
    print(f"[ZeroMQ Receiver] Connecting to tcp://{zmq_host}:{zmq_port}, topic: {zmq_topic}")
    print("[ZeroMQ Receiver] Waiting for XR data... (Press Ctrl+C to exit)")
    print("-" * 80)
    
    # 初始化 ZeroMQ SUB socket
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{zmq_host}:{zmq_port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, zmq_topic)
    
    # 设置接收超时（避免阻塞）
    socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 秒超时
    
    frame_count = 0
    
    try:
        while True:
            try:
                # 接收数据（格式：topic + " " + json_string）
                message = socket.recv_string()
                
                # 分离 topic 和 JSON 数据
                if " " in message:
                    topic, json_str = message.split(" ", 1)
                else:
                    # 如果没有 topic，整个消息就是 JSON
                    topic = ""
                    json_str = message
                
                # 解析 JSON
                packet = json.loads(json_str)
                
                frame_count += 1
                
                # 完整输出：打印完整的 JSON 数据
                print(f"\n[Frame {packet.get('frame_id', 'N/A')}] "
                      f"Timestamp: {packet.get('timestamp', 'N/A'):.3f}")
                print(json.dumps(packet, indent=2, ensure_ascii=False))
                print("-" * 80)
                
            except zmq.Again:
                # 超时，没有收到数据
                print(f"[Warning] No data received within timeout. Is xr_data_forwarder.py running?")
                time.sleep(1)
            except json.JSONDecodeError as e:
                print(f"[Error] Failed to parse JSON: {e}")
            except Exception as e:
                print(f"[Error] Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                
    except KeyboardInterrupt:
        print(f"\n[ZeroMQ Receiver] Interrupted. Total frames received: {frame_count}")
    finally:
        socket.close()
        context.term()
        print("[ZeroMQ Receiver] Closed.")


if __name__ == '__main__':
    # 可以从命令行参数读取配置
    # 用法: python test_zmq_receiver.py [host] [port] [topic]
    # 例如: python test_zmq_receiver.py localhost 5555 xr_raw_data
    zmq_host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    zmq_port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555
    zmq_topic = sys.argv[3] if len(sys.argv) > 3 else "xr_raw_data"
    
    test_zmq_receiver(zmq_host, zmq_port, zmq_topic)

