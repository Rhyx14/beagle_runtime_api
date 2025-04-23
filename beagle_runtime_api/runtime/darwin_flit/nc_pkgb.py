from .flit import Head,Body0,Body1,TailRead,TailSpike,TailWrite,Command
from ctypes import LittleEndianStructure
from .constant import FLIT_TYPE_BODY,FLIT_TYPE_HEAD,FLIT_TYPE_CMD,FLIT_TYPE_TAIL
from .constant import PKG_CMD,PKG_SPIKE,PKG_READ,PKG_WRITE

from .misc import encode_xy_single_board
class CmdPkg(LittleEndianStructure):
    _fields_ = Command._fields_
    def __init__(self, cmd,arg) -> None:
        super().__init__()
        self.arg=arg
        self.cmd=cmd
        self.flit_type_head=FLIT_TYPE_CMD

class SpikePkg(LittleEndianStructure):
    _fields_= Head._fields_ + TailSpike._fields_
    def __init__(self,
                 target_x,target_y,direction,RA,
                 neu_index,dedr_id) -> None:
        super().__init__()
        self.flit_type_head = FLIT_TYPE_HEAD
        self.pkg_class = PKG_SPIKE
        self.RA = RA
        encode_xy_single_board(self,target_x,target_y,direction)

        self.flit_type_tail=FLIT_TYPE_TAIL
        self.neu_index=neu_index
        self.dedr_id=dedr_id


class ReadPkg(LittleEndianStructure):
    _fields_ = Head._fields_ + TailRead._fields_
    def __init__(self,
                 target_x,target_y,via_direction,RA,
                 raddr,RD,relay_link,relay_id) -> None:
        super().__init__()
        self.flit_type_head = FLIT_TYPE_HEAD
        self.pkg_class = PKG_READ
        self.RA = RA
        encode_xy_single_board(self,target_x,target_y,via_direction)

        self.flit_type_tail=FLIT_TYPE_TAIL
        self.raddr=raddr
        self.RD= RD
        self.relay_link=relay_link
        self.relay_id= relay_id

class WritePkg(LittleEndianStructure):
    _fields_= Head._fields_ + Body0._fields_ + Body1._fields_ + TailWrite._fields_
    def __init__(self,
                 target_x,target_y,via_direction,RA,
                waddr,RD,relay_link,relay_id,
                wdata,) -> None:
        self.flit_type_head = FLIT_TYPE_HEAD
        self.pkg_class = PKG_WRITE
        self.RA = RA
        encode_xy_single_board(self,target_x,target_y,via_direction)

        self.waddr=waddr
        self.RD=RD
        self.relay_link=relay_link
        self.relay_id=relay_id
        self.flit_type_body0= FLIT_TYPE_BODY
        
        self.wdata1= wdata >> 24
        self.flit_type_body1= FLIT_TYPE_BODY
        
        self.wdata0 = wdata & 0xFF_FFFF
        self.flit_type_tail= FLIT_TYPE_TAIL 



# class F_FlowFlit():
#     _fields_ = Head._fields_ + TailRead._fields_

# class ShortSpike():
#     _fields_=

# class Reward():
#     _fields_=

# class ShortReward():
#     _fields_=

# class Flow():
#     _fields_=[
#         ("head",Head),
#         ("tail",TailSpike)
#     ]
