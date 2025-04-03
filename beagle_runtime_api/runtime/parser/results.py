# if addr >=0x10000:
#     _cat="dedr"
# elif addr_eff >= 0x8000:
#     _cat = "axon"
# elif addr_eff >= 0x4000:
#     _cat = "wgtsum"
# elif addr_eff >= 0x2000:
#     _cat = "vt"
# elif addr_eff >= 0x1000:
#     _cat = "inst"
# elif addr_eff >= 0x0800:
#     _cat = "reg"
# else:
#     _cat = "conf"

#? expand to int32 integer if needed
# v = _value & 0xffff # tuncate to 16bit
# if v >= 0x8000 and addr_eff >= 0x800 and addr_eff < 0x8000:
#     v = v - 0x10000
from .result_base import ResultBase
class SpikeResult(ResultBase):
    def __init__(self,tik,x,y,dedr_id,neu_idx) -> None:
        super().__init__('spk',tik,x,y)
        self.dedr_id=dedr_id
        self.neu_idx=neu_idx

    def __str__(self) -> str:
        return f'{super().__str__()}, dedr_id=0x{self.dedr_id:04x}, neu_idx=0x{self.neu_idx:03x}'

class RewardResult(ResultBase):
    def __init__(self, tik, x, y,dedr_id,wgt) -> None:
        super().__init__('rwd',tik, x, y)
        self.dedr_id=dedr_id
        self.wgt=wgt
    
    def __str__(self) -> str:
        return f"{super().__str__()}, dedr_id=0x{self.dedr_id:04x}, wgt=0x{self.wgt:02x}"

class FlowResult(ResultBase):
    def __init__(self, tik, x, y,relay_link,data) -> None:
        super().__init__('flow',tik, x, y)
        self.relay_link=relay_link
        self.data=data

    def __str__(self) -> str:
        return f'{super().__str__()}, relay_link=0x{self.relay_link:02x}, data={self.data:018x}'

class MemResult(ResultBase):
    def __init__(self, tik, x, y, relay_link,addr,value) -> None:
        super().__init__('mem',tik, x, y)
        self.relay_link=relay_link
        self.addr=addr
        self.value=value

    def __str__(self) -> str:
        width=32
        if self.addr>=0x800: width=16
        if self.addr>=0x4000: width=26
        if self.addr>=0x10000: width=48
        return f'{super().__str__()}, relay_link=0x{self.relay_link:02x}, addr=0x{self.addr:05x}, value=0x{self.value:0{width//4}x}'