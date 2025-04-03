from .results import MemResult,SpikeResult
# from loguru import logger

_ncls=lambda _x : (
    (_x & 0b1 << 47) >> 47, # OY0
    (_x & 0b1 << 39) >> 39, # EY0
    (_x & 0b111111 << 40) >> 40, # PRT1B-Y
    (_x & 0b111111 << 32) >> 32, # PRT1A-Y
    (_x & 0b1 <<15) >> 15, # OX0
    (_x & 0b1 <<7) >> 7, # EX0
    (_x & 0b1111111 <<8 )>>8, # PRT1B-X
    (_x & 0b1111111), # PRT1A-X
    (_x & 0xFF00_0000) >> 24, # PRT0-R
    (_x & 0x00FF_0000) >> 16, # PRT1-R
)
_ncls_str='[OY0-EY0=%s-%s\tPRT1B-Y=%d\tPRT1A-Y=%d\tOX0-EX0=%s-%s\tPRT1B-X=%d\tPRT1A-X=%d\tPRT0-R=%d\tPRT1-R=%d]'

_ncis=lambda _x : (
    (_x & 0xFFFF_0000_0000)>>32, # i
    (_x &      0xFFFF_0000)>>16, # vth
    (_x &           0xFFFF), # res
    (_x &           0xFF00), #rpd
    (_x &             0xFF), # PAR0
)
_ncis_str='[i=%d\tvth=%d\tres=%d\trpd=%d\tPAR0=%d]'

_ncdedr=lambda _x : (
    (_x & 0xFFFF_0000_0000), # daddr
    (_x & (0b1111 << 44))>>44, # ctype
    (_x & (0b1111_1111_1111 << 32))>>32, # neu_id
    (_x & (0b111 << 29))>>29, # dtype
    (_x & (0b111 << 17))>>17, # len
    (_x & (0b1 << 16)>>16), # share
    (_x & 0b1_1111_1111_1111), # FL
    (_x & (0xFFFF)), #weight
)
_ncdedr_str='[daddr=%d\tctype=%d\tneu_id%d\tdtype=%b\tlen=%d\tshare=%d\tFL=%d\twaddr/wgt=%x]'

def NC_LS(result_list,print_output=False):
    decoded=list([_ncls(_rslt.value) for _rslt in result_list])
    if print_output:
        for _decoded,_rslt in zip(decoded,result_list):
            print(_rslt,_ncls_str % _decoded)
    return decoded

def NC_IS(result_list,print_output=False):
    decoded=list([_ncis(_rslt.value) for _rslt in result_list])
    if print_output:
        for _decoded,_rslt in zip(decoded,result_list):
            print(_rslt,_ncis_str % _decoded)
    return decoded   

def NC_DEDR(result_list,print_output=False):
    decoded=list([_ncdedr(_rslt.value) for _rslt in result_list])
    if print_output:
        for _decoded,_rslt in zip(decoded,result_list):
            print(_rslt,_ncdedr_str % _decoded)
    return decoded

def NC_DEDR_weight(result_list,print_output=False):
    decoded=list([(_rslt.value & 0xFF00_0000_0000) >> 40 for _rslt in result_list])
    return decoded

def spikes(neuron_id_json_list,recvs:list[tuple],tiks:int):
    rslt = [[] for _ in range(tiks)]
    for _recv_flit in recvs:
        if isinstance(_recv_flit,SpikeResult):
            index = f"{_recv_flit.x}, {_recv_flit.y}, {_recv_flit.dedr_id}"
            for _file_name,_neuron_index_json in neuron_id_json_list:
                _info=_neuron_index_json.get(index)
                if _info is not None: rslt[_recv_flit.tik-1].append((_file_name,_info))
    return rslt