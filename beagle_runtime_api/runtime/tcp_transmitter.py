from io import BytesIO
import socket,struct
MAX_FLIT_SIZE = 2 ** 26  # 0.25GB
from loguru import logger
class Transmitter(object):
    """
    用于建立TCP连接的类
    """
    def __init__(self):
        self.socket_inst = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_inst.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def connect_lwip(self, ip_address):
        self.socket_inst.connect(ip_address)

    def close(self):
        self.socket_inst.close()

    def send_flit_bin(self, flit_bin:bytes | bytearray,data_type, directions=0):
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
    
    def recv(self,recv_run_flit_file):
        fout = BytesIO()
        data_len=0
        while True:
            request = self.socket_inst.recv(10240)
            if not request: break # 无数据时退出
            data_len += len(request)
            fout.write(request)
        if data_len % 4 !=0:
            print(f"received data is not intact (with {len})!")
        if recv_run_flit_file is not None:
            recv_run_flit_file.write_bytes(fout.getvalue())
        return fout