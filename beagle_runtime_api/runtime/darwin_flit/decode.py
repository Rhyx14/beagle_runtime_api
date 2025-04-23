from .flit import Head
from .nc_pkgb import SpikePkg,WritePkg,CmdPkg,ReadPkg
from .constant import PKG_FFLOW,PKG_FLOW,PKG_READ,PKG_REWARD,PKG_SHORT_REWARD,PKG_SHORT_SPIKE,PKG_SPIKE,PKG_WRITE
from .constant import FLIT_TYPE_BODY,FLIT_TYPE_HEAD,FLIT_TYPE_CMD,FLIT_TYPE_TAIL
from .result import SpikeResult
from io import BytesIO
def decode(flits_buffer) -> list:
    """
    解析 Darwin3 返回的包
    Args:
        recv_run_flit (str): 返回包的名称
    Returns:
        flit list(解析后)
    """

    tik = 0
    rw_rslt=[]
    read_index=0
    mv= flits_buffer.getbuffer()
    data_length=len(mv)
    while read_index < data_length:
        hd=Head.from_buffer(mv,read_index)
        if hd.flit_type_head == FLIT_TYPE_CMD:
            hd=CmdPkg.from_buffer(mv,read_index)
            if hd.cmd== 0b011000:
                tik = tik + hd.arg + 1 
            read_index+=4
        else:
            _pkg_class=hd.pkg_class
            if _pkg_class == PKG_WRITE:
                _pkg=SpikePkg.from_buffer(mv,read_index)
                read_index += 16

            elif _pkg_class == PKG_READ:
                _pkg=ReadPkg.from_buffer(mv,read_index)
                read_index +=8
                # rw_rslt.append(_pkg)

            elif _pkg_class == PKG_SPIKE : # spikes
                _pkg=SpikePkg.from_buffer(mv,read_index)
                read_index +=8
                rw_rslt.append(SpikeResult(tik,_pkg))

            else:
                raise NotImplementedError(f"unknown pkg_class {_pkg_class}.")
    return rw_rslt