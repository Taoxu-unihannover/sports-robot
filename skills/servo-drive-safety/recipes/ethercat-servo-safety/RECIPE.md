---
name: ethercat-servo-safety
skill: servo-drive-safety
description: EtherCAT 多轴伺服同步与安全驱动功能验收流程。
source:
  docs: https://www.ethercat.org
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# EtherCAT Servo Safety Recipe

## 验收项

1. 读取 Distributed Clocks 同步偏差。
2. 验证 1 kHz 周期下 WKC 稳定。
3. 触发 STO/SS1/SLS，记录力矩切断时间。
4. 注入编码器错误和驱动报警，检查状态机降级。
5. 验证日志不阻塞伺服主环。

