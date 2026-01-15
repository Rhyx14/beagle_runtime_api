from .constant import TYPE_READ_RESULT,TYPE_SPIKE_RESULT,TYPE_WRITE_RESULT,TYPE_CMD_RESULT
from .misc import decode_xy_single_board
from collections import defaultdict
class CmdResult():
    __slots__='type','cmd','arg'
    def __init__(self,raw_pkg) -> None:
        self.type=TYPE_CMD_RESULT
        self.cmd=raw_pkg.cmd
        self.arg=raw_pkg.arg

class SpikeResult():
    __slots__='type','tik','x','y','dedr_id'
    def __init__(self,tik,raw_pkg) -> None:
        self.type=TYPE_SPIKE_RESULT
        self.tik=tik
        self.x,self.y=decode_xy_single_board(raw_pkg)
        self.dedr_id=raw_pkg.dedr_id

    @staticmethod
    def parse_spike(neuron_id_json_list,recvs:list,time_step:int):
        rslt = [[] for _ in range(time_step)]
        for _result in recvs:
            if _result.type==TYPE_SPIKE_RESULT:
                index = (_result.x,_result.y,_result.dedr_id)
                for _file_name,_neuron_index_json in neuron_id_json_list.items():
                    _info=_neuron_index_json.get(index)
                    if _info is not None: rslt[_result.tik].append((_file_name,_info))
        return rslt
    
    @staticmethod
    def parse_spike_single_layer(neuron_id_json,recvs:list,time_step:int):
        rslt = [[] for _ in range(time_step)]
        for _result in recvs:
            if _result.type==TYPE_SPIKE_RESULT:
                rslt[_result.tik].append(neuron_id_json[(_result.x,_result.y,_result.dedr_id)])
        return rslt
    
#     def __str__(self) -> str:
#         return f'{super().__str__()}, dedr_id=0x{self.dedr_id:04x}, neu_idx=0x{self.neu_idx:03x}'

# class RewardResult(ResultBase):
#     def __init__(self, tik, x, y,dedr_id,wgt) -> None:
#         super().__init__('rwd',tik, x, y)
#         self.dedr_id=dedr_id
#         self.wgt=wgt
    
#     def __str__(self) -> str:
#         return f"{super().__str__()}, dedr_id=0x{self.dedr_id:04x}, wgt=0x{self.wgt:02x}"

# class FlowResult(ResultBase):
#     def __init__(self, tik, x, y,relay_link,data) -> None:
#         super().__init__('flow',tik, x, y)
#         self.relay_link=relay_link
#         self.data=data

#     def __str__(self) -> str:
#         return f'{super().__str__()}, relay_link=0x{self.relay_link:02x}, data={self.data:018x}'

class MemResult():
    def __init__(self,raw_pkg) -> None:
        self.type=TYPE_WRITE_RESULT
        self.waddr=raw_pkg.waddr
        self.x,self.y=decode_xy_single_board(raw_pkg)
        self.data0=raw_pkg.wdata0
        self.data1=raw_pkg.wdata1

    def __str__(self) -> str:
        width=32
        if self.waddr>=0x800: width=16
        if self.waddr>=0x4000: width=26
        if self.waddr>=0x10000: width=48
        return f'relay_link=0x{self.relay_link:02x}, addr=0x{self.waddr:05x}, value=0x{self.data0 + self.data1 * (1<<24):0{width//4}x}'
    
    @staticmethod
    def parse_memory(recvs:list,sort=True):
        rslt = defaultdict(list)
        for _result in recvs:
            if _result.type==TYPE_WRITE_RESULT:
                rslt[(_result.x,_result.y)].append((_result.waddr,_result.data0+_result.data1*(1<<24)))
        if sort:
            for _key in rslt.keys():
                rslt[_key].sort(key=lambda x:x[0])
        return rslt
    
    @staticmethod
    def parse_weight(recvs:list,bit_width):
        max_unsigned = 1 << bit_width
        threshold = 1 << (bit_width - 1)
        def unsigned_to_signed(unsigned_val):
            """
            通用的无符号转有符号函数
            """
            # 判断是否超过有符号正数范围
            if unsigned_val < threshold:
                return unsigned_val
            else:
                return unsigned_val - max_unsigned
        rslt = defaultdict(list)
        for _result in recvs:
            if _result.type==TYPE_WRITE_RESULT:
                rslt[(_result.x,_result.y)].append((
                    _result.waddr,
                    unsigned_to_signed(((_result.data0+_result.data1*(1<<24))>>(48-bit_width)))
                ))
            for _key in rslt.keys():
                rslt[_key].sort(key=lambda x:x[0])
        return rslt