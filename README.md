# PyUVM Synchronous FIFO Verification Environment

这是一个基于 **Python (PyUVM + Cocotb)** 构建的同步 FIFO 敏捷验证环境。本项目脱离了传统的 SystemVerilog UVM 框架，利用 Python 的强大生态实现了面向对象的事务级验证，并支持无缝对接各大商业级仿真器（QuestaSim / VCS）。

## 🌟 核心特性

* **纯 Python 驱动**：使用 PyUVM 实现了完整的验证组件（Sequencer, Driver, Monitor, Scoreboard）。
* **黄金参考模型 (Reference Model)**：在 Scoreboard 中利用 Python 原生列表（List）构建了零延迟的理想 FIFO 模型，实现自动化的数据比对。
* **并发压力测试 (狂飙模式)**：利用 `cocotb.start_soon` 协程机制，实现了读写并发乱序注入，覆盖了极端的“全满写”与“全空读”边界场景。
* **跨平台兼容与覆盖率**：通过配置 Makefile，支持一键切换仿真器，并自动生成 HTML 格式的行覆盖率与翻转覆盖率（Toggle Coverage）报告。
* **Emoji 状态日志**：定制了 UTF-8 编码的日志输出系统，终端状态一目了然。

## 📁 目录结构

* `rtl/` : 同步 FIFO 的 Verilog 设计源码。
* `main.py` : PyUVM 验证环境的核心代码，包含 Transaction, Env, Testcases。
* `Makefile` : Cocotb 仿真控制脚本。

## 🚀 快速开始

### 环境依赖
* Python 3.8+
* `cocotb`, `pyuvm` (通过 `pip install pyuvm` 安装)
* 支持 VPI 接口的仿真器 (默认配置为 QuestaSim，也可切换为 VCS/Icarus)

### 运行仿真
进入目录，执行以下命令运行指定的测试用例：

```bash
# 运行基础读写测试
make TESTCASE=test_case0

# 运行读写并发压力测试，并开启覆盖率收集
make TESTCASE=test_case1


### 仿真结果
4680.00ns DEBUG    ..ek3/pyuvm_sync_fifo/main.py(134) [uvm_test_top.env.rd_mon]: 👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: 202
  4680.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(178) [uvm_test_top.env.scb]: ✅ PASS: 成功读出预期数据 202
  4690.00ns INFO     ..eek3/pyuvm_sync_fifo/main.py(59) [uvm_test_top.env.wr_drv]: 📤 [WrDriver] 发起写入: 154
  4690.00ns INFO     ..eek3/pyuvm_sync_fifo/main.py(79) [uvm_test_top.env.wr_mon]: 👀 [WrMonitor] 抓取到成功写入: 154
  4690.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(167) [uvm_test_top.env.scb]: 📦 [Scoreboard] 记录写入数据: 154，当前库存: [231, 56, 154]
  4710.00ns INFO     ..eek3/pyuvm_sync_fifo/main.py(59) [uvm_test_top.env.wr_drv]: 📤 [WrDriver] 发起写入: 57
  4710.00ns INFO     ..eek3/pyuvm_sync_fifo/main.py(79) [uvm_test_top.env.wr_mon]: 👀 [WrMonitor] 抓取到成功写入: 57
  4710.00ns DEBUG    ..ek3/pyuvm_sync_fifo/main.py(134) [uvm_test_top.env.rd_mon]: 👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: 231
  4710.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(167) [uvm_test_top.env.scb]: 📦 [Scoreboard] 记录写入数据: 57，当前库存: [231, 56, 154, 57]
  4710.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(178) [uvm_test_top.env.scb]: ✅ PASS: 成功读出预期数据 231
  4730.00ns INFO     ..eek3/pyuvm_sync_fifo/main.py(59) [uvm_test_top.env.wr_drv]: 📤 [WrDriver] 发起写入: 224
  4730.00ns INFO     ..eek3/pyuvm_sync_fifo/main.py(79) [uvm_test_top.env.wr_mon]: 👀 [WrMonitor] 抓取到成功写入: 224
  4730.00ns DEBUG    ..ek3/pyuvm_sync_fifo/main.py(134) [uvm_test_top.env.rd_mon]: 👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: 56
  4730.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(167) [uvm_test_top.env.scb]: 📦 [Scoreboard] 记录写入数据: 224，当前库存: [56, 154, 57, 224]
  4730.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(178) [uvm_test_top.env.scb]: ✅ PASS: 成功读出预期数据 56
  4750.00ns DEBUG    ..ek3/pyuvm_sync_fifo/main.py(134) [uvm_test_top.env.rd_mon]: 👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: 154
  4750.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(178) [uvm_test_top.env.scb]: ✅ PASS: 成功读出预期数据 154
  4770.00ns DEBUG    ..ek3/pyuvm_sync_fifo/main.py(134) [uvm_test_top.env.rd_mon]: 👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: 57
  4770.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(178) [uvm_test_top.env.scb]: ✅ PASS: 成功读出预期数据 57
  4790.00ns DEBUG    ..ek3/pyuvm_sync_fifo/main.py(134) [uvm_test_top.env.rd_mon]: 👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: 224
  4790.00ns INFO     ..ek3/pyuvm_sync_fifo/main.py(178) [uvm_test_top.env.scb]: ✅ PASS: 成功读出预期数据 224
  5020.00ns INFO     cocotb.regression                  main.test_case1 passed
  5020.00ns INFO     cocotb.regression                  **************************************************************************************
                                                        ** TEST                          STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        **************************************************************************************
                                                        ** main.test_case0                PASS        3220.00           0.04      76633.94  **
                                                        ** main.test_case1                PASS        1800.00           0.05      38558.07  **
                                                        **************************************************************************************
                                                        ** TESTS=2 PASS=2 FAIL=0 SKIP=0               5020.00           0.10      48840.33  **
                                                        **************************************************************************************


