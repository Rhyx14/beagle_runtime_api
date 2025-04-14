import numpy as np
import os,struct
from io import StringIO,BytesIO
from .gen_flit import gen_flit,gen_flit_east,gen_flit_parallel,gen_flit_parallel_east
from .gen_flit_fast import gen_flit_mem_west
from .flit_constant import FLIT_BINARY_LENGTH,FLIT_BINARY_LENGTH_VALUE,FLIT_TEXT_LENGTH,FLIT_BINARY_NUM_VALUE,FLIT_TEXT_LENGTH_BYTE,FLIT_TEXT_NUM_BYTE
from ..dwnc import DWNC
from .flit_gen_status import FlitGenStatus
def gen_flit_by_dwnc_mem_west(cfg_path, dwnc_list: list[tuple], direct=0):
    """
    这个函数gen_flit_by_fn负责根据输入文件（通常是.dwnc文件）生成FLIT数据包，
    FLIT数据包是一种用于神经网络中数据传输的格式，
    它包含了操作类型、目标地址、数据值和其他控制信息。
    对于读操作，它可能需要从其他文件中读取数据并生成对应的FLIT数据包。
    对于写操作，它需要将数据写入FLIT数据包中。
    最后，它使用gen_flit函数生成FLIT数据包，并将这些数据包写入到文本和二进制文件中。
    dwnc_list: dwnc列表
    fin_bin: 要保存到的内存位置（编译完的字节）
    """
    # print("===========================")
    # config_list = {
    #     "last_vc": 1,
    #     "tick": 0,
    #     "start_tick": -1,
    #     "stop_tick": -1,
    #     "clear_tick": -1,
    #     "pkg_num": 0,
    # }
    flit_gen_status=FlitGenStatus(last_vc=1,tick=0,start_tick=-1,stop_tick=-1,clear_tick=-1,pkg_num=0)
    bytes_io=BytesIO()
    for _dwnc in dwnc_list:
        match _dwnc[1]:
            case DWNC.COMMAND.SPIKE | DWNC.COMMAND.CMD:
                gen_flit_mem_west(
                _dwnc,
                bytes_io,
                direct,
                x_from=-1,
                y_from=-1,
                flit_gen_status=flit_gen_status)
            case _:
                raise NotImplementedError
        
    return bytes_io

def gen_flit_by_dwnc_west(cfg_path, dwnc_list: list[str], direct=0):
    """
    这个函数gen_flit_by_fn负责根据输入文件（通常是.dwnc文件）生成FLIT数据包，
    并将这些数据包写入到文本和二进制文件中。
    FLIT数据包是一种用于神经网络中数据传输的格式，
    它包含了操作类型、目标地址、数据值和其他控制信息。
    对于读操作，它可能需要从其他文件中读取数据并生成对应的FLIT数据包。
    对于写操作，它需要将数据写入FLIT数据包中。
    最后，它使用gen_flit函数生成FLIT数据包，并将这些数据包写入到文本和二进制文件中。
    dwnc_list: dwnc列表
    fin_text: 要保存到的内存位置(字符串形式)
    fin_bin: 要保存到的内存位置（编译完的字节）
    """
    # print("===========================")
    config_list = {
        "last_vc": 1,
        "tick": 0,
        "start_tick": -1,
        "stop_tick": -1,
        "clear_tick": -1,
        "pkg_num": 0,
    }
    fin_text=BytesIO()
    fin_bin=BytesIO()
    # cfg_path = Path(self.app_path)/'output_files'
    while config_list.get("config_list") != None:
        config_list = config_list["config_list"]
    for items in dwnc_list:
        item = items.split()
        if len(item) < 2:
            continue
        if "#" in item[0]:
            continue
        # if item[0] == "<<":
        #     self._gen_flit_by_dwnc(
        #         self.config_path / item[1], # TODO
        #         fin_text,
        #         fin_bin,
        #         direct,
        #         cfg_path,
        #         config_list=config_list,
        #     )
        if item[1] == "read" and len(item) >= 6:
            tmp = item
            addr = int(item[4],16)
            item[5] = int(item[5],16)
            for i in range(int(item[5])):
                tmp[4] = "%s" % hex(addr + i)
                gen_flit(
                    tmp,
                    fin_text,
                    fin_bin,
                    direct,
                    x_from=-1,
                    y_from=-1,
                    config_list=config_list,
                )
        elif (
            item[1] == "write"
            or items[1] == "write_ram"
            or item[1] == "read_ack"
            or item[1] == "write_risc"
            or item[1] == "read_risc_ack"
        ) and len(item) == 5:
            if item[1] == "write_ram":
                item[1] = "write"
            tmp = item
            tmp.append("")
            if os.path.exists(cfg_path + item[4]):
                with open(cfg_path / item[4], "rb") as write_f:
                    tot = int.from_bytes(
                        write_f.read(4), byteorder="little", signed=False
                    )
                    for segment in range(tot):
                        area_id = int(write_f.read(1)[0])
                        t = area_id & 0xF
                        config_word_equal = (t & 0x80) != 0
                        addr = int.from_bytes(
                            write_f.read(4), byteorder="little", signed=False
                        )
                        length = int.from_bytes(
                            write_f.read(4), byteorder="little", signed=False
                        )
                        bs = 4
                        di = 1
                        # Dedr
                        if t == 0x01:
                            addr += 0x10000
                            bs = 6
                        # Wgtsum
                        if t == 0x02:
                            addr += 0x4000
                            bs = 2
                        # Inference State
                        if t == 0x03:
                            addr += 0x10000
                            bs = 6
                            di = -1
                        # Voltage
                        if t == 0x04:
                            addr += 0x2000
                            bs = 2
                        # Axon
                        if t == 0x05:
                            addr += 0x8000
                            bs = 4
                        # Learn State
                        if t == 0x06:
                            addr += 0x10000
                            bs = 6
                            di = -1
                        # Inst
                        if t == 0x07:
                            addr += 0x1000
                            bs = 2
                        # Reg
                        if t == 0x08:
                            addr += 0x800
                            bs = 2
                        size = length if config_word_equal else int(length / bs)
                        x, y = int(item[2]), int(item[3])
                        address = np.arange(addr, addr + size * di, di)
                        if config_word_equal:
                            value = struct.unpack_from(
                                "<Q", write_f.read(bs) + b"\x00" * (8 - bs)
                            )[0]
                            text_buffer = bytes(FLIT_TEXT_LENGTH)
                            binary_buffer = bytes(
                                FLIT_BINARY_LENGTH
                            )
                            gen_flit_parallel(
                                x,
                                y,
                                address,
                                value,
                                text_buffer,
                                0,
                                binary_buffer,
                                0,
                                config_list=config_list,
                            )
                            text_buffer = text_buffer * size
                            binary_buffer = binary_buffer * size
                        else:
                            buffer = write_f.read(length)
                            index_byte = np.arange(0, length, bs)
                            text_buffer = bytearray(
                                size * FLIT_TEXT_LENGTH
                            )
                            text_offset = np.arange(
                                0,
                                size * FLIT_TEXT_LENGTH,
                                FLIT_TEXT_LENGTH,
                            )
                            binary_buffer = bytearray(
                                size * FLIT_BINARY_LENGTH
                            )
                            binary_offset = np.arange(
                                0,
                                size * FLIT_BINARY_LENGTH,
                                FLIT_BINARY_LENGTH,
                            )
                            def convert(
                                x,
                                y,
                                address,
                                index_byte,
                                text_offset,
                                binary_offset,
                            ):
                                buffer_value = buffer[
                                    index_byte : index_byte + bs
                                ] + b"\x00" * (8 - bs)
                                value = struct.unpack("<Q", buffer_value)[0]
                                gen_flit_parallel(
                                    x,
                                    y,
                                    address,
                                    value,
                                    text_buffer,
                                    text_offset,
                                    binary_buffer,
                                    binary_offset,
                                    config_list=config_list,
                                )
                            np.frompyfunc(convert, 6, 0)(
                                x,
                                y,
                                address,
                                index_byte,
                                text_offset,
                                binary_offset,
                            )
                        fin_text.write(text_buffer)
                        fin_bin.write(binary_buffer)
        elif (
            item[1] == "write"
            or item[1] == "write_ram"
            or item[1] == "read_ack"
            or item[1] == "write_risc"
            or item[1] == "read_risc_ack"
        ) and os.path.exists(cfg_path / item[5]):
            if item[1] == "write_ram":
                item[1] = "write"
            tmp = item
            x, y = int(item[2]), int(item[3])
            addr = int(item[4],16)
            with open(cfg_path / item[5], "r") as write_f:
                wlines = write_f.readlines()
                wlength = len(wlines)
                address = np.arange(addr, addr + wlength)
                text_buffer = bytearray(
                    wlength * FLIT_TEXT_LENGTH
                )
                text_offset = np.arange(
                    0,
                    wlength * FLIT_TEXT_LENGTH,
                    FLIT_TEXT_LENGTH,
                )
                binary_buffer = bytearray(
                    wlength * FLIT_BINARY_LENGTH
                )
                binary_offset = np.arange(
                    0,
                    wlength * FLIT_BINARY_LENGTH,
                    FLIT_BINARY_LENGTH,
                )
                def convert(x, y, address, line, text_offset, binary_offset):
                    return gen_flit_parallel(
                        x,
                        y,
                        address,
                        int(line, 16),
                        text_buffer,
                        text_offset,
                        binary_buffer,
                        binary_offset,
                        config_list=config_list,
                    )
                np.frompyfunc(convert, 6, 0)(
                    x, y, address, wlines, text_offset, binary_offset
                )
                fin_text.write(text_buffer)
                fin_bin.write(binary_buffer)
        else:
            gen_flit(
                item,
                fin_text,
                fin_bin,
                direct,
                x_from=-1,
                y_from=-1,
                config_list=config_list,
            )
    return fin_text,fin_bin