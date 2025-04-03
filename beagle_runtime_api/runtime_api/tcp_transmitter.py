import socket,struct
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

    def send_flit_bin(self, flit_bin_file, data_type):
        """
        发送flit
        """
        with open(flit_bin_file, "rb") as file:
            flit_bin = file.read()
        length = len(flit_bin) >> 2
        if length > 2**26:
            print("====== %s is larger than 0.25GB" % flit_bin_file)
            print("====== send flit length failed")
            return 0
        send_bytes = bytearray()
        send_bytes += struct.pack("I", length)
        send_bytes += struct.pack("I", data_type)
        send_bytes += flit_bin
        self.socket_inst.sendall(send_bytes)
        return 1

    def send_flit_bin_quick(self, flit_bin, data_type):
        """
        发送flit
        """
        # with open(flit_bin_file, "rb") as file:
            # flit_bin = file.read()
        length = len(flit_bin) >> 2
        if length > 2**26:
            print("====== data is larger than 0.25GB")
            print("====== send flit length failed")
            return 0
        send_bytes = bytearray()
        send_bytes += struct.pack("I", length)
        send_bytes += struct.pack("I", data_type)
        send_bytes += flit_bin
        self.socket_inst.sendall(send_bytes)
        return 1