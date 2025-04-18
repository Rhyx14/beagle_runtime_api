TYPE_SPIKE_RESULT=0
TYPE_READ_RESULT=1
TYPE_WRITE_RESULT=2

class SpikeResult():
    __slots__='type','tik','x','y','dedr_id'
    def __init__(self,tik,from_x,from_y,raw_pkg) -> None:
        self.type=TYPE_SPIKE_RESULT
        self.tik=tik
        self.x=from_x
        self.y=from_y
        self.dedr_id=raw_pkg.dedr_id

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