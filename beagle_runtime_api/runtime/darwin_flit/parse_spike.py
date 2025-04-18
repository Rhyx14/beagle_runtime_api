from .result import TYPE_SPIKE_RESULT
def parse_spike(neuron_id_json_list,recvs:list,tiks:int):
    rslt = [[] for _ in range(tiks)]
    for _result in recvs:
        if _result.type==TYPE_SPIKE_RESULT:
            # index = f"{_result.x}, {_result.y}, {_result.dedr_id}"
            index = (_result.x,_result.y,_result.dedr_id)
            for _file_name,_neuron_index_json in neuron_id_json_list:
                _info=_neuron_index_json.get(index)
                if _info is not None: rslt[_result.tik-1].append((_file_name,_info))
    return rslt