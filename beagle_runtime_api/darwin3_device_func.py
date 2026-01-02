import struct,struct
from io import BytesIO
from pathlib import Path
from functools import reduce

from .compiler_model import CompilerModel

from .transmitter.tcp_transmitter import TCPTransmitter

from .darwin_flit.decode import decode
from .darwin_flit.encode import encode
from .darwin_flit.constant import PKG_WRITE,PKG_WRITE,PKG_SPIKE,PKG_CMD,PKG_READ
from .darwin_flit.command_list import CommandList
from .dma_direction import WEST,EAST,NORTH,SOUTH

def gen_spike_input_dwnc(
    input_neuron_info: dict,
    neuron_spike_list: list,
) -> CommandList:
    """
    input_neuron.json && length of spike_neurons (list) => spikes.dwnc
    跟据spikes.dwnc以及config文件中提到的神经元，生成对应的run_input.dwnc文件
    Args:
        neuron_spike_list (list): 输入的神经元脉冲序列
    Returns:
        dwnc list
    """
    dwnc_list=CommandList([(PKG_CMD,0,1)]) # open time step
    gap_spikes=0
    for _i in range(0, len(neuron_spike_list)):
        cur_spike_neuron_list = neuron_spike_list[_i]
        
        if len(cur_spike_neuron_list)==0:
            gap_spikes+=1
        else:
            dwnc_list.append((PKG_CMD,0b011000,gap_spikes)) # step timestep
            gap_spikes=0
        for spike_neuron in cur_spike_neuron_list:
            neuron_info = input_neuron_info[str(spike_neuron)]
            if len(neuron_info) > 0:
                neuron_type = neuron_info[0]
                targets_list = neuron_info[-1]
                if neuron_type == 0:
                    neu_idx = neuron_info[1]
                elif neuron_type == 1:
                    neu_idx = 0x0
                for target in targets_list:
                    dwnc_list.append((PKG_SPIKE,target[0],target[1],neu_idx,target[2]))
        # dwnc_list.append((PKG_CMD,0b011000,0)) # step 1
    if gap_spikes>0: # process tail empty spike list
        dwnc_list.append((PKG_CMD,0b011000,gap_spikes-1))
    dwnc_list.append((PKG_CMD,0,0)) # turn off
    return dwnc_list


def gen_deploy_flitin(compiled_model: CompilerModel,hardare_step: int) -> tuple[CommandList,CommandList]:
    """
    *-*-config.dwnc => deploy_input.dwnc
    Args:
        deploy_input_dwnc_file (str): 生成的 dwnc 文件的名称
    Returns:
        None
    """
    # 东西向传输
    west_dwnc_list=CommandList(entry=WEST)
    east_dwnc_list=CommandList(entry=EAST)

    # 清除神经元推理状态和权重和
    for _x,_y in compiled_model.used_neuron_cores.keys():
        if _x <= 15: 
            west_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x5)) # 清空
        else:
            east_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x5))
    for _cmd_list in compiled_model.used_neuron_cores.values():
        if _cmd_list.entry==WEST: west_dwnc_list.extend(_cmd_list)
        if _cmd_list.entry==EAST: east_dwnc_list.extend(_cmd_list)

    # 加入开启/停止tik控制对 => 代表配置结束
    west_dwnc_list.append((PKG_CMD,0,1))
    west_dwnc_list.append((PKG_CMD,0,0))
    east_dwnc_list.append((PKG_CMD,0,1))
    east_dwnc_list.append((PKG_CMD,0,0))

    # 设置hardware_step_size
    west_dwnc_list.append((PKG_CMD,0b100000,hardare_step))
    east_dwnc_list.append((PKG_CMD,0b100000,hardare_step))
    # 清除神经元推理状态和权重和

    for _x,_y in compiled_model.used_neuron_cores.keys():
        if _x <= 15:
            west_dwnc_list.append((PKG_WRITE,_x,_y,0x15,0x1)) # 使能
            west_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x1)) # 清空
        else:
            east_dwnc_list.append((PKG_WRITE,_x,_y,0x15,0x1))
            east_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x1))
    return west_dwnc_list,east_dwnc_list

    
def excute_dwnc_command(device,dwnc_list,direction,type,saving_name='',recv=True,saving_recv=False) -> tuple[int,list] | None:
    if isinstance(dwnc_list,CommandList):
        bin_io_rslt=dwnc_list.encode()
    else:
        bin_io_rslt=encode(dwnc_list,direction)
    # send
    # Path.write_bytes(Path(self._cache_path/'beagle_run_flits_in.bin'),bin_io_rslt)
    rslt = device.transmitter.transmit_flit(direction, 
                        data_type=type,
                        flit_bin=bin_io_rslt,
                        recv=recv,
                        recv_run_flit_file=None if not saving_recv else device._cache_path / f"recv_{saving_name}.txt")
    if recv:
        max_tik_index,rslt = decode(rslt)
        return max_tik_index,rslt
    
def excute_dwnc_command_prof(device,secretary,dwnc_list,direction,type,saving_name='',recv=True,saving_recv=False) -> list | None:
    with secretary.flame_time('compile spike'):
        if isinstance(dwnc_list,CommandList):
            bin_io_rslt=dwnc_list.encode()
        else:
            bin_io_rslt=encode(dwnc_list,direction)
    # send
    # Path.write_bytes(Path(self._cache_path/'beagle_run_flits_in.bin'),bin_io_rslt)
    with secretary.flame_time('hardware running'):
        rslt = device.transmitter.transmit_flit(direction, 
                            data_type=type,
                            flit_bin=bin_io_rslt,
                            recv=recv,
                            recv_run_flit_file=None if not saving_recv else device._cache_path / f"recv_{saving_name}.txt")
    if recv:
        with secretary.flame_time('decompile spike'):
            max_tik_index,rslt = decode(rslt)
        return max_tik_index,rslt
        