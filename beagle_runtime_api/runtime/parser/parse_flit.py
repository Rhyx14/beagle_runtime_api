from .results import ResultBase,MemResult,SpikeResult,FlowResult,RewardResult
def parse_flit(recv_run_flit:str, log=False) -> list:
    """
    解析 Darwin3 返回的包
    Args:
        recv_run_flit_file (str): 返回包的名称
        result (list(list)): spike的解析结果
        log (bool): 是否输出到控制台
    Returns:
        flit list(解析后)
    """
    lines=recv_run_flit.split('\n')
    index = 0
    is_write_read = 0
    is_spike = 0
    is_reward = 0
    is_flow = 0
    t = 0
    # if debug:
        # fanalyse = open(file_path+recv_run_flit_file+'_'+pop_name+'_analyse.txt','w')
    rw_rslt=[]
    for _flit in lines:
        if _flit=='' : continue
        _flit_type=int(_flit[0],16)>>2&0x3    
        if _flit_type == 3:  #flit_type=3 
            cmd = int(_flit[0:2], 16)&0x3f    #[31:26]
            if cmd == 0b011000:     # d8000000
                arg = int(_flit[2:8],16)
                t+=arg+1
        elif _flit_type == 2 :    #flit_type=2 包头
            index = 0
            _pak_class = int(_flit[1:3],16)>>2
            is_write_read = _pak_class & 0x7 == 1    #[24:22]
            is_spike = _pak_class & 0x7 in (0,4,5,6)
            is_reward= _pak_class & 0x7 in (5,6)
            is_flow  = _pak_class & 0x7 == 7
            _dst = int(_flit[3:5],16)
            dst_x = (_dst>>2) & 0xf    #[17:14]
            if (_dst>>6) & 0x1 == 1:     #[18]
                dst_x = -dst_x
            y = (int(_flit[0:2],16)>>1)&0x1f     #[29:25]
            x = ((int(_flit[5:7],16)>>1)&0xf) + dst_x - 1    #[8:5]
        elif (is_write_read == 1) :
            if _flit_type == 1 :
                _value = (_value<<24) + ((int(_flit[0:8],16)>>3)&0x7ffffff)
                addr_eff = addr & 0x1ffff
                addr_relay = (addr >> 18) & 0x3f
                
                rw_rslt.append(MemResult(t,x,y,addr_relay,addr_eff,_value))
                is_write_read = 0
            elif _flit_type == 0 : #?
                if (index == 0):
                    addr = (int(_flit[0:8],16)>>3)&0x7ffffff
                    index = index + 1
                else :
                    _value = (int(_flit[0:8],16)>>3)&0x7ffffff
        elif (is_spike == 1) :
            if _flit_type == 1 :      #flit_type=1 包尾
                neu_idx = (int(_flit[4:8],16) >> 3) & 0xfff  #[29:15]
                dedr_id = (int(_flit[0:5],16) >> 3) & 0x7fff  #[14:3]
                if is_reward:
                    rw_rslt.append(RewardResult(t,x,y,dedr_id,neu_idx))
                else:
                    rw_rslt.append(SpikeResult(t,x,y,dedr_id,neu_idx))
                is_spike = 0
                is_reward = 0
        elif (is_flow == 1) :
            if _flit_type == 1 :
                addr_relay = (addr >> 18) & 0x3f
                data = data + ((int(_flit[0:8],16)&0x3fffffff)<<24)
                data = (data << 17) + (addr & 0x1ffff)
                rw_rslt.append(FlowResult(t,x,y,addr_relay,data))
                is_flow = 0
            elif _flit_type == 0 :
                if (index == 0):
                    addr = (int(_flit[9:16],16)>>3)&0x7ffffff
                    index = index + 1
                else :
                    data = (int(_flit[0:8],16)>>3)&0x7ffffff
    if log: 
        for _rslt in rw_rslt: print(_rslt)
    return rw_rslt