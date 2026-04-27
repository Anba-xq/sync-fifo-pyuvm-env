import cocotb
from pyuvm import *
from cocotb.triggers import RisingEdge, ReadOnly, Timer, ClockCycles
from cocotb.clock import Clock
import random
import logging

# ===================================================================
# 1. Transaction
# ===================================================================
class FifoItem(uvm_sequence_item):
    def __init__(self,name,data=0):
        super().__init__(name)
        self.data = data

# ===================================================================
# 2. Write 侧组件
# ===================================================================
class WrSeq(uvm_sequence):
    async def body(self):
        # --- 第一阶段：顺序值测试（19个数据) ---
        for i in range(1,20):
            item = FifoItem(f"wr_item_{i}",data = (i *10)%256)
            await self.start_item(item)
            await self.finish_item(item)

            # --- 第二阶段：随机压力测试 (50个数据) ---
        for i in range(50):
            # 产生 0-255 的随机数据
            rand_val = random.randint(0,255)
            # 产生随机名字，方便在日志里区分
            item = FifoItem(f"wr_random_{i}",data = rand_val)
            await self.start_item(item)
            await self.finish_item(item)
            if random.random() > 0.6:
                wait_cycles = random.randint(1,2)
                await ClockCycles(cocotb.top.clk,wait_cycles)

class WrDriver(uvm_driver):
    def build_phase(self):
        self.dut = ConfigDB().get(self,"","DUT")

    async def run_phase(self):
        # 初始状态设为不写
        self.dut.wr_en.value = 0
        self.dut.wr_data.value = 0
        while True:
            await ReadOnly()  # 等待当前时刻电平稳定
            if self.dut.rst_n.value == 0:
                await RisingEdge(self.dut.clk)
                continue
            item = await self.seq_item_port.get_next_item()
            await RisingEdge(self.dut.clk)

            # 如果不满，才拉高写使能并给出数据
            if self.dut.full.value == 0:
                self.dut.wr_en.value = 1
                self.dut.wr_data.value = item.data
                self.logger.info(f"📤 [WrDriver] 发起写入: {item.data}")
            self.seq_item_port.item_done()

            # 写完一个后，把使能拉低一个周期
            await RisingEdge(self.dut.clk)
            self.dut.wr_en.value = 0

class WrMonitor(uvm_monitor):
    def build_phase(self):
        self.dut = ConfigDB().get(self,"","DUT")
        self.ap = uvm_analysis_port("wr_ap",self)

    async def run_phase(self):
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()

            if self.dut.full.value == 0 and self.dut.wr_en.value == 1:
                val = int(self.dut.wr_data.value)
                self.ap.write(FifoItem("mon_wr",val))
                self.logger.info(f"👀 [WrMonitor] 抓取到成功写入: {val}")

# ===================================================================
# 3. Read 侧组件
# ===================================================================
class RdSeq(uvm_sequence):
    async def body(self):
        # 尝试读 N 次
        for i in range(80):
            item = FifoItem(f"rd_req")
            await self.start_item(item)
            await self.finish_item(item)
            if random.random() > 0.8:
                await ClockCycles(cocotb.top.clk, random.randint(1, 2))

class RdDriver(uvm_driver):
    def build_phase(self):
        self.dut = ConfigDB().get(self,"","DUT")
    async def run_phase(self):
        self.dut.rd_en.value = 0
        while True:
            await ReadOnly()  # 等待当前时刻电平稳定
            if self.dut.rst_n.value == 0:
                await RisingEdge(self.dut.clk)
                continue
            item = await self.seq_item_port.get_next_item()
            await RisingEdge(self.dut.clk)
            if self.dut.empty.value == 0 :
                self.dut.rd_en.value = 1
            self.seq_item_port.item_done()
            await RisingEdge(self.dut.clk)
            self.dut.rd_en.value = 0

class RdMonitor(uvm_monitor):
    def build_phase(self):
        self.dut = ConfigDB().get(self, "", "DUT")
        self.ap = uvm_analysis_port("rd_ap", self)
        self.logger.setLevel(logging.DEBUG)
    async def run_phase(self):
        # 增加一个标志位，用来记忆“上一拍有没有发过读命令”
        read_happened = False

        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()

            # 如果当前正在复位，清空记忆，不发数
            if self.dut.rst_n.value == 0:
                read_happened = False
                continue

            # 如果上一拍发起了有效的读操作，那么这一拍引脚上的数据就是新鲜出炉的！
            if read_happened:
                val = int(self.dut.rd_data.value)
                self.ap.write(FifoItem("mon_rd", val))
                self.logger.debug(f"👀 [RdMonitor] 抓取到延迟一拍的新鲜数据: {val}")

            # 检查当前这一拍是否有有效的读命令，设置标志位，留给下一拍去抓数据
            if self.dut.rd_en.value == 1 and self.dut.empty.value == 0:
                read_happened = True
            else:
                read_happened = False

# ===================================================================
# 4. Scoreboard 侧组件
# ===================================================================
class FifoScoreboard(uvm_scoreboard):
    def build_phase(self):
        # 准备两个收件箱
        self.wr_fifo = uvm_tlm_analysis_fifo("wr_fifo",self)
        self.rd_fifo = uvm_tlm_analysis_fifo("rd_fifo",self)
        # 【Reference Model】用 Python 列表模拟一个无限大的黄金 FIFO
        self.ref_model = []
    def flush(self):
        # 清空参考模型，用于复位后的同步
        self.ref_model.clear()
        while self.wr_fifo.can_get():
            self.wr_fifo.flush()
        while self.rd_fifo.can_get():
            self.rd_fifo.flush()
    async def run_phase(self):
        cocotb.start_soon(self.monitor_write())
        cocotb.start_soon(self.monitor_read())

    async def monitor_write(self):
        while True:
            item = await self.wr_fifo.get()
            self.ref_model.append(item.data)
            self.logger.info(f"📦 [Scoreboard] 记录写入数据: {item.data}，当前库存: {self.ref_model}")

    async def monitor_read(self):
        while True:
            item = await self.rd_fifo.get()  # 如果有人往外读
            if len(self.ref_model) == 0:
                self.logger.error(f"❌ FAIL: 硬件读出了 {item.data}，但参考模型里是空的！")
            else:
                # 拿 Python 列表最老的数据 (索引0) 进行比对
                expected = self.ref_model.pop(0)
                if expected == item.data:
                    self.logger.info(f"✅ PASS: 成功读出预期数据 {item.data}")
                else:
                    self.logger.error(f"❌ FAIL: 期望 {expected}, 实际 {item.data}")

# ======================================================================
# 5. Env & Test 组装
# ======================================================================
class FifoEnv(uvm_env):
    def build_phase(self):
        # 实例化组件
        self.wr_seqr = uvm_sequencer("wr_seqr", self)
        self.wr_drv = WrDriver("wr_drv", self)
        self.wr_mon = WrMonitor("wr_mon", self)

        self.rd_seqr = uvm_sequencer("rd_seqr", self)
        self.rd_drv = RdDriver("rd_drv", self)
        self.rd_mon = RdMonitor("rd_mon", self)

        self.scb = FifoScoreboard("scb", self)

    def connect_phase(self):
        # 连接 Driver 和 Sequencer
        self.wr_drv.seq_item_port.connect(self.wr_seqr.seq_item_export)
        self.rd_drv.seq_item_port.connect(self.rd_seqr.seq_item_export)
        # 将 Monitor 大喇叭接给 Scoreboard 收件箱
        self.wr_mon.ap.connect(self.scb.wr_fifo.analysis_export)
        self.rd_mon.ap.connect(self.scb.rd_fifo.analysis_export)

# ======================================================================
# 6. 基础测试类：把公共的组装和复位逻辑抽出来
# ======================================================================
class FifoTestBase(uvm_test):
    def build_phase(self):
        ConfigDB().set(None, "*", "DUT",cocotb.top)
        self.env = FifoEnv("env", self)

    async def reset_out(self):
        """ 公共的硬件复位方法 """
        dut  = cocotb.top
        dut.rst_n.value = 0
        dut.wr_en.value = 0
        dut.rd_en.value = 0
        await Timer(20, unit="ns")
        dut.rst_n.value = 1
        await RisingEdge(dut.clk)

@test()
class test_case0(FifoTestBase):
    async def run_phase(self):
        dut = cocotb.top
        cocotb.start_soon(Clock(dut.clk,10,unit="ns").start())
        self.raise_objection()
        await self.reset_out()  # 调用父类的方法

        wr_seq = WrSeq("wr_seq")
        rd_seq = RdSeq("rd_seq")

        self.logger.info("🚀 ========================================")
        self.logger.info("🎬 开始运行 test_case0: 串行测试 (先写后读)")
        self.logger.info("🚀 ========================================")

        await wr_seq.start(self.env.wr_seqr)
        await rd_seq.start(self.env.rd_seqr)

        await cocotb.triggers.ClockCycles(dut.clk, 10)
        self.drop_objection()

# ----------------------------------------------------------------------
# 用例 1：并发狂飙测试 (边写边读)
# ----------------------------------------------------------------------
@test()
class test_case1(FifoTestBase):
    async def run_phase(self):
        dut = cocotb.top
        # 注意：每个 Test 启动时都是一次全新的仿真，所以还要重新起时钟和复位
        cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
        self.raise_objection()

        await self.reset_out()

        wr_seq = WrSeq("wr_seq")
        rd_seq = RdSeq("rd_seq")

        self.logger.info("⚡ =========================================")
        self.logger.info("🔥 开始运行 test_case1: 并发测试 (狂飙模式)")
        self.logger.info("⚡ =========================================")

        wr_task = cocotb.start_soon(wr_seq.start(self.env.wr_seqr))
        rd_task = cocotb.start_soon(rd_seq.start(self.env.rd_seqr))

        await wr_task
        await rd_task

        await ClockCycles(dut.clk, 10)
        self.drop_objection()
        if len(self.env.scb.ref_model) != 0:
            self.logger.warning(f"⚠️ 仿真结束，但参考模型里还剩 {len(self.env.scb.ref_model)} 个数据！")


