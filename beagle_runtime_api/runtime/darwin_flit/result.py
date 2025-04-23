from .constant import TYPE_READ_RESULT,TYPE_SPIKE_RESULT,TYPE_WRITE_RESULT
from .misc import decode_xy_single_board
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
                # index = f"{_result.x}, {_result.y}, {_result.dedr_id}"
                index = (_result.x,_result.y,_result.dedr_id)
                for _file_name,_neuron_index_json in neuron_id_json_list:
                    _info=_neuron_index_json.get(index)
                    if _info is not None: rslt[_result.tik-1].append((_file_name,_info))
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

# class MemResult(ResultBase):
#     def __init__(self, tik, x, y, relay_link,addr,value) -> None:
#         super().__init__('mem',tik, x, y)
#         self.relay_link=relay_link
#         self.addr=addr
#         self.value=value

#     def __str__(self) -> str:
#         width=32
#         if self.addr>=0x800: width=16
#         if self.addr>=0x4000: width=26
#         if self.addr>=0x10000: width=48
#         return f'{super().__str__()}, relay_link=0x{self.relay_link:02x}, addr=0x{self.addr:05x}, value=0x{self.value:0{width//4}x}'