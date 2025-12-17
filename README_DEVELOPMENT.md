# 开发工作流

## Git 工作流说明

### 后续开发

在开发分支上进行修改后，提交并推送：

```bash
git add .
git commit -m "fix: 修复坐标转换问题"
git push  # 因为已经设置了 upstream，直接 push 即可
```

### 同步原仓库更新

如果需要同步原仓库的最新更新到你的 fork：

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

### 合并更新到开发分支

将主分支的更新合并到你的开发分支：

```bash
git checkout feature/quest3-botyard-integration
git merge main
```

## 常用环境与网络tips

### pip 下载过慢时的加速建议

如果在安装依赖时（例如 `pip install -e .`）下载非常慢，可以临时加上清华镜像源参数：

```bash
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## XR 最小联调测试（Meta Quest 3）

本节记录目前已经跑通的 **最小 XR 通路测试**，只验证「Quest3 ↔ PC ↔ televuer/tv_wrapper」，**不依赖 Unitree 机器人和 SDK**，方便后续随时复现实验。

### 前置条件

- 已在 `tv` conda 环境中完成 `xr_teleoperate` 的基础安装（参考官方 `README_zh-CN.md` 中的 1.1 章节）
- 已在 `teleop/televuer` 目录下执行过：

  ```bash
  pip install -e .
  ```

- 已生成 `key.pem` / `cert.pem` 证书，并按官方说明复制到 `~/.config/xr_teleoperate/` 或通过环境变量 `XR_TELEOP_CERT` / `XR_TELEOP_KEY` 指定

### 步骤一：PC 端启动 tv_wrapper 测试

在 PC 上（建议用 `tv` 环境）执行：

```bash
conda activate tv
cd ~/botyard_ws/src/xr_teleoperate/teleop/televuer
python test/test_tv_wrapper.py
```

- 看到类似提示即可（IP 以实际环境为准）：

  ```text
  Request to 192.168.xxx.xxx:60000 timed out or no response, using local config.
  Loaded camera config from local cam_config_server.yaml
  Press Enter to start tv_wrapper test...
  Serving file:///.../televuer at /static
  Visit: https://vuer.ai?grid=False
  ```

- 此时 **先不要按回车**，等待 XR 设备连上后再开始循环。

### 步骤二：查询 PC 内网 IP

在 PC 终端中执行：

```bash
ifconfig
```

- 找到无线网卡（例如 `wlo1`）对应的 `inet` 字段，例如：

  ```text
  wlo1: ...
      inet 192.168.0.127  netmask 255.255.255.0  broadcast 192.168.0.255
  ```

- 记下这里的 IP（示例中为 `192.168.0.127`），后面在 Quest3 浏览器中使用。

### 步骤三：Quest3 浏览器连接 Vuer 页面

1. 确保 Quest3 与 PC 处于**同一 Wi‑Fi 网段**（如 `192.168.0.x`）
2. 在 Quest3 中打开浏览器，访问：

   ```text
   https://<PC_IP>:8012/?ws=wss://<PC_IP>:8012
   ```

   示例（PC IP 为 `192.168.0.127`）：

   ```text
   https://192.168.0.127:8012/?ws=wss://192.168.0.127:8012
   ```

3. 首次访问时浏览器会提示证书不安全：
   - 选择 **Advanced / 高级**
   - 再选择 **Proceed to IP (unsafe) / 继续访问（不安全）**

4. 进入页面后，点击页面中的 **`Virtual Reality`** 按钮，按提示允许浏览器访问头显的必要权限（摄像头 / 运动 / 位置等）。

### 步骤四：PC 端开始读取 XR 数据

回到 PC 上运行 `test_tv_wrapper.py` 的终端，**按一次回车键**，开始主循环：

- 终端会持续打印类似如下的 `TeleData` 快照：

  ```text
    17:34:12:702281 INFO     ---- TV Wrapper TeleData ----                                       test_tv_wrapper.py:48
    17:34:12:702487 INFO     -------------------=== TeleData Snapshot ===-------------------     test_tv_wrapper.py:51
    17:34:12:702589 INFO     [Head Pose]:                                                        test_tv_wrapper.py:52
                            [[ 0.80240267 -0.26709106 -0.53367817 -0.08690728]                                       
                            [ 0.21298822  0.96353323 -0.16198679  0.03037623]                                       
                            [ 0.55748189  0.01631147  0.83002889  0.9308233 ]                                       
                            [ 0.          0.          0.          1.        ]]                                      
    17:34:12:702666 INFO     [Left Wrist Pose]:                                                  test_tv_wrapper.py:53
                            [[ 4.80937570e-01  1.94562316e-01  8.54894519e-01  4.03422998e-01]                       
                            [-3.73992771e-01  9.27431345e-01 -6.73786155e-04  1.79278429e-02]                       
                            [-7.92987049e-01 -3.19400281e-01  5.18801510e-01 -1.86352842e-01]                       
                            [ 0.00000000e+00  0.00000000e+00  0.00000000e+00  1.00000000e+00]]                      
    17:34:12:702729 INFO     [Right Wrist Pose]:                                                 test_tv_wrapper.py:54
                            [[ 0.91321063 -0.24729082  0.3238728   0.53191871]                                       
                            [ 0.33096543 -0.01353737 -0.94354582 -0.07619467]                                       
                            [ 0.2377146   0.9688468   0.06948223  0.21638117]                                       
                            [ 0.          0.          0.          1.        ]]                                      
    17:34:12:702742 INFO     [Left Trigger Value]: 10.00                                         test_tv_wrapper.py:71
    17:34:12:702752 INFO     [Left Squeeze Value]: 0.00                                          test_tv_wrapper.py:72
    17:34:12:702782 INFO     [Left Thumbstick Value]: [0. 0.]                                    test_tv_wrapper.py:73
    17:34:12:702791 INFO     [Left A/B Buttons]: A=0, B=0                                        test_tv_wrapper.py:74
    17:34:12:702799 INFO     [Right Trigger Value]: 10.00                                        test_tv_wrapper.py:76
    17:34:12:702806 INFO     [Right Squeeze Value]: 0.00                                         test_tv_wrapper.py:77
    17:34:12:702832 INFO     [Right Thumbstick Value]: [0. 0.]                                   test_tv_wrapper.py:78
    17:34:12:702842 INFO     [Right A/B Buttons]: A=0, B=0                                       test_tv_wrapper.py:79
    [TeleVuer] Warning: render_to_xr is ignored when webrtc is enabled or pass_through is True.
    17:34:12:718312 INFO     main process sleep: 0.015382734298706055                            test_tv_wrapper.py:86
    ```

- 这表示：
  - Vuer / televuer 服务正常启动
  - Quest3 通过浏览器成功连接到 PC
  - `TeleVuerWrapper` 正在持续接收 XR 侧的头部、手柄/手势数据

如需结束测试，在该终端按 `Ctrl + C` 即可安全退出。


## XR 数据转发（ZeroMQ）

将 XR 原始数据通过 ZeroMQ 转发，供 ROS2 或其他进程接收。

### 启动顺序

**重要：必须按以下顺序启动**

1. **启动数据转发器（先不要按回车）**
   ```bash
   conda activate tv
   unset PYTHONPATH
   cd ~/botyard_ws/src/xr_teleoperate/teleop/televuer/test
   python xr_data_forwarder.py
   ```
   看到 `Press Enter to start XR data forwarder...` 后，**先不要按回车**。

2. **Quest3 连接网页端**
   - 在 Quest3 浏览器访问：`https://<PC_IP>:8012/?ws=wss://<PC_IP>:8012`
   - 点击 **Virtual Reality** 按钮，允许权限

3. **在转发器终端按回车**
   - 回到 PC 终端，按回车开始数据转发

### 配置说明

- 默认 ZeroMQ 端口：`5555`
- 默认 topic：`xr_raw_data`
- 数据格式：JSON，包含所有原始 XR 数据（位姿、控制器/手势数据等）

### 测试接收

```bash
cd ~/botyard_ws/src/xr_teleoperate/teleop/televuer/test
python3 test_zmq_receiver.py
```

或指定 IP 和端口：
```bash
python3 test_zmq_receiver.py <host> <port> <topic>
```

接收端会完整打印每帧的 JSON 数据。

