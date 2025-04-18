from .flit import Head,Body0,Body1,TailRead,TailSpike,TailWrite,Command
from ctypes import LittleEndianStructure
from .flit import FLIT_TYPE_BODY,FLIT_TYPE_HEAD,FLIT_TYPE_CMD,FLIT_TYPE_TAIL
PKG_SPIKE=0
PKG_WRITE=1
PKG_READ=2
PKG_FFLOW=3
PKG_SHORT_SPIKE=4
PKG_REWARD=5
PKG_SHORT_REWARD=6
PKG_FLOW=7

class CmdPkg(LittleEndianStructure):
    _fields_ = Command._fields_
    def __init__(self, arg,cmd) -> None:
        super().__init__()
        self.arg=arg
        self.cmd=cmd
        self.flit_type_head=FLIT_TYPE_CMD

class SpikePkg(LittleEndianStructure):
    _fields_= Head._fields_ + TailSpike._fields_
    def __init__(self,
                 route_id,dst_port,dst_x,dst_y,src_x,src_y,RA,
                 neu_index,dedr_id) -> None:
        super().__init__()
        self.flit_type_head = FLIT_TYPE_HEAD
        self.route_id = route_id
        self.pkg_class = PKG_SPIKE
        self.dst_port = dst_port

        if dst_x > 0:
            self.dst_x_sign=0
            self.dst_x = dst_x
        else:
            self.dst_x_sign=1
            self.dst_x = -dst_x
        if dst_y > 0:
            self.dst_y_sign=0
            self.dst_y = dst_y
        else:
            self.dst_y_sign=1
            self.dst_y = -dst_y 

        self.src_x = src_x
        self.src_y = src_y
        self.RA = RA

        self.flit_type_tail=FLIT_TYPE_TAIL
        self.neu_index=neu_index
        self.dedr_id=dedr_id
        pass

class ReadPkg(LittleEndianStructure):
    _fields_ = Head._fields_ + TailRead._fields_
    def __init__(self,
                 route_id,dst_port,dst_x,dst_y,src_x,src_y,RA,
                 raddr,RD,relay_link,relay_id) -> None:
        super().__init__()
        self.flit_type_head = FLIT_TYPE_HEAD
        self.route_id = route_id
        self.pkg_class = PKG_READ
        self.dst_port = dst_port

        if dst_x > 0:
            self.dst_x_sign=0
            self.dst_x = dst_x
        else:
            self.dst_x_sign=1
            self.dst_x = -dst_x
        if dst_y > 0:
            self.dst_y_sign=0
            self.dst_y = dst_y
        else:
            self.dst_y_sign=1
            self.dst_y = -dst_y 

        self.src_x = src_x
        self.src_y = src_y
        self.RA = RA

        self.flit_type_tail=FLIT_TYPE_TAIL
        self.raddr=raddr
        self.RD= RD
        self.relay_link=relay_link
        self.relay_id= relay_id
        pass

class WritePkg(LittleEndianStructure):
    _fields_= Head._fields_ + Body0._fields_ + Body1._fields_ + TailWrite._fields_
    def __init__(self,
                route_id,dst_port,dst_x,dst_y,src_x,src_y,RA,
                waddr,RD,relay_link,relay_id,
                wdata,) -> None:
        self.flit_type_head = FLIT_TYPE_HEAD
        self.route_id = route_id
        self.pkg_class = PKG_WRITE
        self.dst_port = dst_port

        if dst_x > 0:
            self.dst_x_sign=0
            self.dst_x = dst_x
        else:
            self.dst_x_sign=1
            self.dst_x = -dst_x
        if dst_y > 0:
            self.dst_y_sign=0
            self.dst_y = dst_y
        else:
            self.dst_y_sign=1
            self.dst_y = -dst_y 

        self.src_x = src_x
        self.src_y = src_y
        self.RA = RA

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
