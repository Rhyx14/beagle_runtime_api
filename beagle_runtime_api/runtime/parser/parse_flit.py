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

def parse_flit_bin_obsolete(recv_run_flit:bytes, log=False) -> list:
    """
    解析 Darwin3 返回的包
    Args:
        recv_run_flit_file (str): 返回包的名称
        result (list(list)): spike的解析结果
        log (bool): 是否输出到控制台
    Returns:
        flit list(解析后)
    """
    # lines=recv_run_flit.split('\n')
    nc_pkgb_body = 0
    is_write_read = 0
    is_spike = 0
    is_reward = 0
    is_flow = 0
    tik = 0
    # if debug:
        # fanalyse = open(file_path+recv_run_flit_file+'_'+pop_name+'_analyse.txt','w')
    rw_rslt=[]
    for _i in range(0,len(recv_run_flit),4):
        _flit=struct.unpack_from('I',recv_run_flit,_i)[0]
        _flit_type= _flit >>30

        if _flit_type == 3:  #flit_type=3 命令包
            cmd = (_flit >> 24) &0b11_1111    #[24:29]
            if cmd == 0b011000:     # d8000000
                arg = _flit & 0xff_ffff # [0:23]
                tik+=arg+1
        
        elif _flit_type == 2 :    #flit_type=2 包头
            nc_pkgb_body = 0
            _pkg_class = (_flit >> 22) & 0b111 #[22:24]
            is_write_read = _pkg_class in (1,2)
            is_spike = _pkg_class in (0,4,5,6) # 重复reward?
            is_reward= _pkg_class in (5,6)
            is_flow  = _pkg_class == 7

            dst_x = (_flit>>14) & 0b1111    #[14:17]
            if ((_flit >> 18) & 1) == 1: # [18] 
                dst_x = -dst_x
            y = (_flit >>25) & 0b1_1111     #[25:29], route_id
            x = (_flit >>5 & 0xf) + dst_x - 1  #[8:5], src_x # 这里如何计算包的位置？
        
        elif (is_write_read == 1) :
            if _flit_type == 1 : # 包尾
                _value = (_value<<24) + (_flit>>3) & 0x7ff_ffff # _value 高24位 + 当前包尾的低24位
                waddr = addr & 0x1_ffff
                relay_link = (addr >> 18) & 0b11_1111
                
                rw_rslt.append(MemResult(tik,x,y,relay_link,waddr,_value))
                is_write_read = 0

            elif _flit_type == 0 : # 包体 ================================
                if (nc_pkgb_body == 0):
                    addr = _flit>>3 & 0x7ff_ffff
                    nc_pkgb_body = 1
                else :
                    _value = _flit>>3 &0x7ff_ffff # _value 高24位 wdata0

        elif (is_spike == 1) :
            if _flit_type == 1 :      #flit_type=1 包尾
                neu_idx = (_flit >> 3) & 0xfff  #[3:14]
                dedr_id = (_flit >> 15) & 0b0111_1111_1111_1111  #[15:29]
                if is_reward:
                    rw_rslt.append(RewardResult(tik,x,y,dedr_id,neu_idx))
                else:
                    rw_rslt.append(SpikeResult(tik,x,y,dedr_id,neu_idx))
                is_spike = 0
                is_reward = 0

        elif (is_flow == 1) :
            if _flit_type == 1 :
                relay_link = (addr >> 18) & 0b11_1111
                data = data + (_flit & 0x3fff_ffff)<<24  # 低到高： 包尾24 + 包体1-24 + 包体0-17
                data = (data << 17) + (addr & 0x1ffff) # 
                rw_rslt.append(FlowResult(tik,x,y,relay_link,data))
                is_flow = 0
            elif _flit_type == 0 :
                # if (index == 0):
                #     addr = (int(_flit[9:16],16)>>3)&0x7ffffff # [9:16]什么东西？
                #     index = index + 1
                # else :
                #     data = (int(_flit[0:8],16)>>3)&0x7ffffff
                if (nc_pkgb_body == 0):
                    addr = _flit>>3 & 0x7ff_ffff
                    nc_pkgb_body = 1
                else :
                    data = _flit>>3 &0x7ff_ffff # 高24位, wdata1
    if log: 
        for _rslt in rw_rslt: print(_rslt)
    return rw_rslt