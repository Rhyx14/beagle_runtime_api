import numpy as np
from functools import reduce
from ..dma_direction import WEST
from .constant import PKG_CMD,PKG_READ,PKG_FLOW,PKG_SPIKE,PKG_WRITE
from .nc_pkgb import CmdPkg,WritePkg,ReadPkg,SpikePkg

LENTH_PKG=[8 for _ in range(20)]
LENTH_PKG[PKG_CMD]=4
LENTH_PKG[PKG_WRITE]=16

def encode(dwnc_list: list[tuple], direction=WEST) -> bytearray:
    """
    encode dwnc into pkgb list (binary array)
    """
    buffer_length= reduce(lambda x,_dwnc: x + LENTH_PKG[_dwnc[0]],dwnc_list,0)
    buffer = bytearray(buffer_length)
    offset=0
    for _dwnc in dwnc_list:
        _type= _dwnc[0]
        if _type == PKG_CMD: # (type, cmd ,arg)
            CmdPkg.from_buffer(buffer,offset).__init__(_dwnc[1],_dwnc[2])

        elif _type == PKG_WRITE: # (type, x,y, waddr, wdata)
            WritePkg.from_buffer(buffer,offset).__init__(
                _dwnc[1],_dwnc[2],direction, 0, _dwnc[3], 0, 0, 0, _dwnc[4]
            )
            
        elif _type == PKG_READ: # (type, x, y, raddr)
            ReadPkg.from_buffer(buffer,offset).__init__(
                _dwnc[1],_dwnc[2],direction,0,_dwnc[3], 0, 0, 0
            )

        elif _type == PKG_SPIKE: # (type,x,y, n_id,d_id)
            SpikePkg.from_buffer(buffer,offset).__init__(
                _dwnc[1],_dwnc[2],direction,0,_dwnc[3],_dwnc[4]
            )

        else: 
            raise NotImplementedError
        offset += LENTH_PKG[_type]
    return buffer