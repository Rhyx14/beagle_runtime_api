from io import BytesIO
import socket,struct
from loguru import logger
from pathlib import Path
from ..flit_type import FlitType
from .transmitter_base import TransmitterBase

MAX_FLIT_SIZE = 2 ** 26  # 0.25GB

class TCPTransmitter(TransmitterBase):
    """
    用于建立TCP连接的类
    """
    def __init__(self,ip,port:list):
        super().__init__()
        self.ip=ip
        self.direction_port_list=port

    def connect_lwip(self, ip_address):
        self.socket_inst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_inst.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket_inst.connect(ip_address)

    def send_flit_bin(self, flit_bin:bytes | bytearray,data_type):
        """
        发送flit
        """
        length = len(flit_bin) >> 2
        if length > MAX_FLIT_SIZE:
            logger.error("flit size is larger than 0.25GB, send flit length failed!")
            return 1
        send_bytes = bytearray()
        send_bytes += struct.pack("II", length,data_type)
        # send_bytes += struct.pack("I", data_type)
        # send_bytes += flit_bin
        self.socket_inst.sendall(send_bytes + flit_bin)
        return 0
    
    def recv(self):
        fout = BytesIO()
        data_len=0
        while True:
            request = self.socket_inst.recv(10240)
            if not request: break # 无数据时退出
            data_len += len(request)
            fout.write(request)
        if data_len % 4 !=0:
            logger.error(f"received data is not intact (with {len})!")
        return fout
    
    def transmit_flit(self, direction, data_type, flit_bin:bytearray=b'', recv=False, recv_run_flit_file : Path=None) -> BytesIO:
        """
        发包到darwin3, recv=True时接收darwin3返回来的包
        Args:
            port (list(int)): TCP 连接端口列表
            data_type (int): 发送包的格式
            freq (int): 设置的时钟频率 (仅当 data_type==SET_FREQUENCY 时有效)
            fbin (str): 发送的包内容 (仅当 data_type==NORMAL_FLIT 时有效)
            recv (bool): 是否接受 Darwin3 的返回包
            recv_run_flit_file (str): 保存返回包的名称
            debug (bool): 调试标记
        Returns:
            None
        """
        self.connect_lwip((self.ip, self.direction_port_list[direction]))
        match data_type:
            case FlitType.CHIP_RESET:
                self.socket_inst.sendall(struct.pack('II', 0x0000,data_type))
                print("[control] reset succeed")
            case FlitType.SET_FREQUENCY:
                self.socket_inst.sendall(struct.pack('II', 333,data_type))
                print("[control] set frequency succeed")
            case _ :
                self.send_flit_bin(flit_bin, data_type)
        if recv:
            fout=self.recv()
            if recv_run_flit_file is not None:
                recv_run_flit_file.write_bytes(fout.getvalue())
        else: fout=BytesIO()
        # self.close()
        self.socket_inst.close()
        return fout