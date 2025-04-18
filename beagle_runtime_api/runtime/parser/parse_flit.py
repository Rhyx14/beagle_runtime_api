from .results import ResultBase,MemResult,SpikeResult,FlowResult,RewardResult
import struct

def parse_flit_bin(recv_flits:bytes) -> list:
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
    data_length=len(recv_flits)
    while read_index < data_length:
        if data_length-read_index < 8:
            _flit_head=struct.unpack_from('I',recv_flits,read_index)[0]            
        else:
            _flit_head,_flit_next=struct.unpack_from('II',recv_flits,read_index)
        read_index +=8

        _flit_type= _flit_head >>30
        if _flit_type ==3: # 命令包
            cmd = (_flit_head >> 24) &0b11_1111    #[24:29]
            if cmd == 0b011000:     # d8000000
                arg = _flit_head & 0xff_ffff # [0:23]
                tik+=arg+1
            read_index -=4
        
        elif _flit_type == 2 :    #flit_type=2 包头    
            _pkg_class = (_flit_head >> 22) & 0b111 #[22:24]
            _dst_x = (_flit_head>>14) & 0b1111    #[14:17]
            if ((_flit_head >> 18) & 1) == 1: # [18] 
                _dst_x = -_dst_x
            _from_y = (_flit_head >>25) & 0b1_1111     #[25:29], route_id
            _from_x = (_flit_head >>5 & 0xf) + _dst_x - 1  #[8:5], src_x # 这里如何计算包的位置？

            match _pkg_class:
                case 1: # write
                    _pkgb_body0 = _flit_next
                    _pkgb_body1,_pkgb_rear=struct.unpack_from('II',recv_flits,read_index)
                    read_index+=8
                    # body 0
                    _relay_id = (_pkgb_body0 >> 27 ) & 0b111
                    _relay_link = (_pkgb_body0 >> 21) & 0b11_1111
                    _rd= (_pkgb_body0 >>20) & 1
                    _waddr = _pkgb_body0 >> 3 & 0x1_ffff
                    # body 1
                    _wdata1 = (_pkgb_body1>>3 & 0xff_ffff)
                    # rear
                    _wdata0 = (_pkgb_rear >> 3) & 0xff_ffff
                    # data load
                    _wdata= _wdata1 << 24 + _wdata0

                    rw_rslt.append(MemResult(tik,_from_x,_from_y,_relay_link,_waddr,_wdata))

                case 2: # read
                    _pkgb_rear=_flit_next
                    _relay_id = (_pkgb_rear >> 27 ) & 0b111
                    _relay_link = (_pkgb_rear >> 21) & 0b11_1111
                    _rd= (_pkgb_rear >>20) & 1
                    _raddr = _pkgb_rear >> 3 & 0x1_ffff
                    raise NotImplementedError

                case 0 | 4 : # spikes
                    _pkgb_rear=_flit_next
                    # rear
                    _neu_idx = (_pkgb_rear >> 3) & 0xfff  #[3:14]
                    _dedr_id = (_pkgb_rear >> 15) & 0b0111_1111_1111_1111  #[15:29]
                    rw_rslt.append(SpikeResult(tik,_from_x,_from_y,_dedr_id,_neu_idx))

                case 5 | 6: # reward
                    _pkgb_rear=_flit_next
                    # rear
                    _neu_idx = (_pkgb_rear >> 3) & 0xfff  #[3:14]
                    _dedr_id = (_pkgb_rear >> 15) & 0b0111_1111_1111_1111  #[15:29]
                    rw_rslt.append(RewardResult(tik,_from_x,_from_y,_dedr_id,_neu_idx))

                case 7: # flow
                    _pkgb_body0 = _flit_next
                    _pkgb_body1,_pkgb_rear=struct.unpack_from('II',recv_flits,read_index)
                    read_index+=8
                    # body 0
                    _relay_id = (_pkgb_body0 >> 27 ) & 0b111
                    _relay_link = (_pkgb_body0 >> 21) & 0b11_1111
                    _rd= (_pkgb_body0 >>20) & 1
                    _waddr = _pkgb_body0 >> 3 & 0x1_ffff
                    # body 1
                    _wdata1 = (_pkgb_body1>>3 & 0xff_ffff)
                    # rear
                    _wdata0 = (_pkgb_rear >> 3) & 0xff_ffff
                    # data load
                    _wdata= _wdata0 << (24+17) + _wdata1<<24 + _waddr

                    rw_rslt.append(MemResult(tik,_from_x,_from_y,_relay_link,_waddr,_wdata))
                    pass
                
                case _:
                    raise NotImplementedError
    return rw_rslt