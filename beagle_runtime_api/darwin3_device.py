import struct,os, json, logging, shutil
import logging,os,json,glob,re,struct,time
from io import StringIO,BytesIO
from pathlib import Path
from functools import reduce

from .compiler_model import CompilerModel

from .tcp_transmitter import Transmitter

from .darwin_flit.decode import decode
from .darwin_flit.encode import encode
from .darwin_flit.result import SpikeResult
from .darwin_flit.constant import PKG_WRITE,PKG_WRITE,PKG_SPIKE,PKG_CMD,PKG_READ,WEST,EAST
from .darwin_flit.command_list import CommandList

try: 
    import torch
except ImportError as e:
    print('PyTorch is not installed, ensure that no torch-API is used!')

class FlitType():
    CHIP_RESET = 10
    SET_FREQUENCY = 11
    NORMAL_FLIT = 0x8000
    CLEAR_STATE = 0x8001
    RESET_SPIKING_INPUT= 0x8002

class darwin3_device(object):
    """
    用于和Darwin3开发板进行通信的类
    """

    def __init__(
        self, 
        protocol="TCP", 
        ip=['172.31.111.35'], 
        port=[6000, 6001], 
        step_size=100000, 
        app_path:Path | str="../", 
        log_debug=False, 
        **kwds,
    ):
        """
        
        Args:
            protocol (str):   与 Darwin3 开发板通信使用的协议, 默认 TCP, 可选 LOCAL, 暂不支持其它
            ip (list(str)):   Darwin3 板卡设备 ip 序列, 单芯片开发板最多支持两个 ip
                              默认使用 ip[0] 进行上下位机通信 (暂不支持 ip[1] 的连接)
                              (因为有两张网卡, 以太网接口和type-C接口均可使用)
            port (list(int)): 与 Darwin3 开发板通信使用的端口, 默认为 6000 和 6001
                              其中 port[0] 为和 Darwin3 west 端 DMA 进行通信的端口
                              port[0] 为和 Darwin3 east 端 DMA 进行通信的端口
                              最多支持 4 个端口, 对面 DMA 的四个通道 (目前仅支持 2 个)
            step_size (int):  每个时间步维持的 FPGA 时钟周期数, 对应时长为 10ns * step_size * 2
                              (汇编工具介绍与上位机通信流程中有换算关系，对应run_input.dwnc中最开始的配置)
            app_path (str):   模型文件的存储目录, 存储目录格式如下所示
            .
            └── app_path (name user-defined)
                ├── beagle_cache # 临时缓存文件夹
                └── config_files
                    ├── 0-1-config.dwnc
                    ├── 0-1-ax.txt
                    ├── 0-1-de.txt
                    ├── 0-2-config.dwnc
                    ├── 0-2-ax.txt
                    ├── 0-2-de.txt
                    ├── 1-1-config.dwnc
                    ├── 1-1-ax.txt
                    ├── 1-1-de.txt
                    ├── input_neuron.json
                    ├── pop_h_1.json
                    ├── pop_h_2.json
                    ├── output_neuron_xxx.json
                    └── ...
        """
        if log_debug:
            logging.basicConfig(level=logging.DEBUG,  # 设置最低日志级别为 DEBUG
                    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
                    filename='app.log',  # 将日志输出到文件 app.log
                    filemode='w')  # 'a'表示追加模式，'w'表示覆盖模式
        
        self.log_debug = log_debug
        # protocol (str): 和 Darwin3 的连接方式
        self.protocol = protocol
        # ip (str): 和 Darwin3 进行 TCP 连接的 IP 地址
        # port (list(int)): 和 Darwin3 进行 TCP 连接的端口号序列
        if self.protocol == "LOCAL":
            self.ip = "127.0.0.1"
        else:
            self.ip = ip[0]
        self.port = port

        # step_size (int): 时间步长度
        self._hardware_step_size = step_size

        # app_path (str): 存储应用的目录
        self.app_path=Path(app_path)

        # 输入输出目录，包括临时缓存
        self._cache_path=self.app_path / 'beagle_cache'
        if self._cache_path.exists():
            print("[WARNING] removing previous cache folder")
            shutil.rmtree(str(self._cache_path))

        Path.mkdir(self._cache_path,exist_ok=True,parents=True)

        self.clear_state_had_started = False

        self.model=CompilerModel(self.app_path / "config_files")
        return

    def reset_freq(self,freq=333):
        '''
        复位硬件接口相关逻辑和硬件系统(darwin3 芯片, DMA 等), 重设时钟
        Args: 
            None
        Returns:
            None
        '''
        self._transmit_flit(port=self.port[0], data_type=FlitType.CHIP_RESET)
        self._transmit_flit(port=self.port[0], data_type=FlitType.SET_FREQUENCY)
        print("[INFO] Reset chip complete, please check the output on the Darwin3 development board.")

    def reset(self,freq=333):
        """
        [obsolete]
        复位硬件接口相关逻辑和硬件系统(darwin3 芯片, DMA 等)
        Args: 
            None
        Returns:
            None
        """
        self._transmit_flit(port=self.port[0], data_type=FlitType.CHIP_RESET)
        print("Please check the output on the Darwin3 development board.")
        return
    
    def darwin3_init(self, freq=333):
        """
        [obsolete]
        按照指定频率配置 darwin3 芯片。
        Args:
            freq (int): 兼容参数，无实际作用
        Returns:
            None
        """
        self._transmit_flit(port=self.port[0], data_type=FlitType.SET_FREQUENCY)
        print("Please check the output on the Darwin3 development board.")
        return
    
    def _transmit_flit(self, port, data_type, flit_bin:bytearray=b'', recv=False, recv_run_flit_file : Path=None) -> BytesIO:
        """
        发包到darwin3, recv=True时接收darwin3返回来的包
        Args:
            port (list(int)): TCP 连接端口列表
            data_type (int): 发送包的格式
            freq (int): 设置的时钟频率 (仅当 data_type==SET_FREQUENCY 时有效)
            fbin (str): 发送的包内容 (仅当 data_type==NORMAL_FLIT 时有效)
            recv (bool): 是否接受 Darwin3 的返回包
            recv_run_flit_file (str): 保存返回包的名称
            debug (bool): 调试标记
        Returns:
            None
        """
        trans = Transmitter()
        trans.connect_lwip((self.ip, port))

        match data_type:
            case FlitType.CHIP_RESET:
                trans.socket_inst.sendall(struct.pack('II', 0x0000,data_type))
                print("[control] reset succeed")
            case FlitType.SET_FREQUENCY:
                trans.socket_inst.sendall(struct.pack('II', 333,data_type))
                print("[control] set frequency succeed")
            case _ :
                trans.send_flit_bin(flit_bin, data_type)

        if recv: fout=trans.recv(recv_run_flit_file)
        else: fout=BytesIO()
        trans.close()

        return fout

    def _gen_spike_input_dwnc(
        self,
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
                neuron_info = self.model.input_neuron[str(spike_neuron)]
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

    def _excute_dwnc_command(self,dwnc_list,direction,type,saving_name='',recv=True,saving_recv=False) -> list | None:
        if isinstance(dwnc_list,CommandList):
            bin_io_rslt=dwnc_list.encode()
        else:
            bin_io_rslt=encode(dwnc_list,direction)
        # send
        # Path.write_bytes(Path(self._cache_path/'beagle_run_flits_in.bin'),bin_io_rslt)
        rslt = self._transmit_flit(port=self.port[0] if direction==WEST else self.port[1], 
                            data_type=type,
                            flit_bin=bin_io_rslt,
                            recv=recv,
                            recv_run_flit_file=None if not saving_recv else self._cache_path / f"recv_{saving_name}.txt")
        if recv:
            max_tik_index,rslt = decode(rslt)
            return max_tik_index,rslt
        
    def clear_neurons_states(self, ISC=False, LSC=False, clear=True, dwnc_file=None):
        """
        清理 darwin3 芯片内部神经拟态核心的状态量
        Args:
            ISC   (bool): inference status clear,
                          推理状态中电流清零, 阈值和振荡电位复位, 1 有效
                          相关配置寄存器: dedr_vth_keep, dedr_vth_gset, 
                          global_vth, dedr_res_keep, global_res
            LSC   (bool): learn status clear, 学习状态清零, 1 有效
            clear (bool): 权重和清零, 膜电位复位, 1 有效
                          相关配置寄存器:vt_rest
                          
            dwnc_file (str): 是否保存cls flit包, 非None保存
        Returns:
            None
        """
        # 根据需要重置的内容生成指令
        if CommandList.global_list.get('cls') is None: 
            clear_type = int(''.join(str(int(b)) for b in [ISC, LSC, clear]), 2)

            west_dwnc_list=CommandList(entry=WEST)
            east_dwnc_list=CommandList(entry=EAST)

            west_dwnc_list.append((PKG_CMD,0,1))
            east_dwnc_list.append((PKG_CMD,0,1))

            for _x,_y in self.model.used_neuron_cores.keys():
                if _x <= 15: west_dwnc_list.append((PKG_WRITE,_x,_y,0x04,clear_type)) # 清空
                else:        east_dwnc_list.append((PKG_WRITE,_x,_y,0x04,clear_type))

            west_dwnc_list.extend(self.model.clear_is_west)
            east_dwnc_list.extend(self.model.clear_is_east)
            
            for key,value in self.model.delay_neuron.items():
                coord = eval(key)
                if coord[0] <= 15:
                    west_dwnc_list.append((PKG_WRITE,coord[0],coord[1],0x00800+value[0], value[1]))
                    west_dwnc_list.append((PKG_WRITE,coord[0],coord[1],0x00800+value[2], value[3]))
                else:
                    east_dwnc_list.append((PKG_WRITE,coord[0],coord[1],0x00800+value[0], value[1]))
                    east_dwnc_list.append((PKG_WRITE,coord[0],coord[1],0x00800+value[2], value[3]))

            west_dwnc_list.append((PKG_CMD,0,0))
            east_dwnc_list.append((PKG_CMD,0,0))

            CommandList.global_list['cls']=(west_dwnc_list,east_dwnc_list)

            if dwnc_file is not None:
                west_dwnc_list.encode()
                west_dwnc_list.save(self._cache_path / "west_cls.txt")
                east_dwnc_list.encode()
                east_dwnc_list.save(self._cache_path / "east_cls.txt")
        else:
            west_dwnc_list,east_dwnc_list=CommandList.global_list['cls']

        self._excute_dwnc_command(west_dwnc_list,WEST,FlitType.NORMAL_FLIT,'cls_west',recv=False,saving_recv=False)
        self._excute_dwnc_command(east_dwnc_list,EAST,FlitType.NORMAL_FLIT,'cls_east',recv=False,saving_recv=False)

        return

    def _gen_deploy_flitin(self):
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
        for _x,_y in self.model.used_neuron_cores.keys():
            if _x <= 15: 
                west_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x5)) # 清空
            else:
                east_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x5))

        for _cmd_list in self.model.used_neuron_cores.values():
            if _cmd_list.entry==WEST: west_dwnc_list.extend(_cmd_list)
            if _cmd_list.entry==EAST: east_dwnc_list.extend(_cmd_list)

        # 加入开启/停止tik控制对 => 代表配置结束
        west_dwnc_list.append((PKG_CMD,0,1))
        west_dwnc_list.append((PKG_CMD,0,0))

        east_dwnc_list.append((PKG_CMD,0,1))
        east_dwnc_list.append((PKG_CMD,0,0))

        # 设置hardware_step_size
        west_dwnc_list.append((PKG_CMD,0b100000,self._hardware_step_size))
        east_dwnc_list.append((PKG_CMD,0b100000,self._hardware_step_size))

        # 清除神经元推理状态和权重和
        for _x,_y in self.model.used_neuron_cores.keys():
            if _x <= 15:
                west_dwnc_list.append((PKG_WRITE,_x,_y,0x15,0x1)) # 使能
                west_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x1)) # 清空
            else:
                east_dwnc_list.append((PKG_WRITE,_x,_y,0x15,0x1))
                east_dwnc_list.append((PKG_WRITE,_x,_y,0x04,0x1))

        return west_dwnc_list,east_dwnc_list

    def deploy_config(self,save=False):
        """
        在部署芯片上部署并使能相关核心, 同时清除神经元的相关状态
        Args:
            None
        Returns:
            None
        """
        dwnc_west,dwnc_east=self._gen_deploy_flitin()
        if save:
            dwnc_west.encode()
            dwnc_west.save(self._cache_path / 'deploy_west.txt')
            dwnc_east.encode()
            dwnc_east.save(self._cache_path/ 'deploy_east.txt')
        self._excute_dwnc_command(dwnc_west,WEST,FlitType.NORMAL_FLIT,'deploy_west',recv=True)
        self._excute_dwnc_command(dwnc_east,EAST,FlitType.NORMAL_FLIT,'deploy_east',recv=True)
        # self._excute_dwnc_command(dwnc_east,EAST,'deploy',recv=False)

    def run_darwin3_withoutfile(self,spike_neurons):
        '''
        obselete api
        '''
        return self.run_darwin3_with_spikes(spike_neurons)

    def run_darwin3_withfile(self,spike_neurons):
        '''
        obselete api
        '''
        return self.run_darwin3_with_spikes(spike_neurons)

    def run_darwin3_with_spikes(self, spike_list: list,saving_input=False,saving_recv=False,print_log=False):
        """
        接收应用给的 spike_list 作为输入，运行 len(spike_list) 个时间步
        Args:
            spike_list (list): sequence, 本次应用输入给硬件的脉冲数据, 
                                  序列长度与时间步数量一致，没有脉冲的时间步给空值

            [
                [0,1,2], # neuron 0,1,2 fired at tick=0
                [0,1], # neuron 0,1 fired at tick=1
            ]
        Returns:
            result (list): 本次运行结束时硬件返回给应用的脉冲
        """
        # 生成spike的dwnc
        dwnc_list=self._gen_spike_input_dwnc(spike_list)
        if saving_input:
            dwnc_list.encode()
            dwnc_list.save(self._cache_path / 'run_input_dwnc.txt')

        max_tik_index,rslt=self._excute_dwnc_command(
            dwnc_list,
            WEST,
            FlitType.NORMAL_FLIT,
            'run_flitin',
            True,
            saving_recv)

        return SpikeResult.parse_spike(self.model.output_neuron_info_jsons,rslt,max_tik_index+1)
    
    def run_with_torch_tensor(self,spike_tensor,output_layer_name,expect_output_shape:tuple,extra_time_steps=0,saving_input=False,saving_recv=False,print_log=False,clear_state=False):
        """
        接收应用给的 PyTorch Tensor
        Args:
            spike_tensor: in [t x], 注意batch_size必须为1
        Returns:
            result tensor: in [t x] 本次运行结束时硬件返回给应用的脉冲
        """
        if len(spike_tensor.shape) >2:
            spike_tensor=spike_tensor.flatten(1)
        t,_=spike_tensor.shape
        spike_list=[]
        for _i in range(t):
            spike_list.append(torch.where(spike_tensor[_i]==1)[0].tolist())
        
        for _ in range(extra_time_steps): spike_list.append([])

        # 生成spike的dwnc
        dwnc_list=self._gen_spike_input_dwnc(spike_list)
        if saving_input:
            (self._cache_path / 'run_input_dwnc.txt').write_text('\n'.join(dwnc_list))

        max_tik_index,rslt=self._excute_dwnc_command(
            dwnc_list,
            WEST,
            FlitType.RESET_SPIKING_INPUT if clear_state else FlitType.NORMAL_FLIT,
            'run_flitin',
            True,
            saving_recv)            

        rslt=SpikeResult.parse_spike_single_layer(self.model.output_neuron_info_jsons[output_layer_name],rslt,max_tik_index+1)
        
        target_t = expect_output_shape[0]
        target_x = reduce(lambda x,y : x*y, expect_output_shape[1:],1)
        # target_t,target_x=expect_output_shape
        output_spike=torch.zeros(target_t,target_x)
        rslt=rslt[-target_t:]
        for _t,_spike_ids in enumerate(rslt):
            if len(_spike_ids)==0: continue
            output_spike[_t,torch.tensor(_spike_ids)]=1
        
        return output_spike.view(*expect_output_shape)

    def dump_memory(self,dump_request:list[tuple]) -> tuple[list]:
        '''
        dump the memory of the specific neuromorphic core.
        ---
        @dump_request: 
        
            list of tuple:(

                nc_position: nc core coordinate, (x,y)

                length : words to be read, int

                offset : words offset, int

                inverse: read in reverse order, bool

            )

        @log: log to console

        @saving_dwnc_path: saving intermediate files
        '''
        # raise NotImplementedError
        # construct dwnc list
        west_dwnc_list=CommandList(entry=WEST)
        east_dwnc_list=CommandList(entry=EAST)

        west_dwnc_list.append((PKG_CMD,0,1))
        east_dwnc_list.append((PKG_CMD,0,1))
        # x,y=nc_position
        for (_x,_y), _length, _offset, _inverse in dump_request:
            if _inverse:
                _addr_iter=range(_offset,_offset-_length,-1)
            else:
                _addr_iter=range(_offset,_offset+_length)

            for _2_addr in _addr_iter:
                _cmd=(PKG_READ,_x,_y,_2_addr)
                # cmd = f"0 read {_x} {_y} {hex(_2_addr)} 1\n"
                if _x>=15:
                    east_dwnc_list.append(_cmd)
                else:
                    west_dwnc_list.append(_cmd)

        west_dwnc_list.append((PKG_CMD,0,0))
        east_dwnc_list.append((PKG_CMD,0,0))
        
        rslt_east= self._excute_dwnc_command(east_dwnc_list,EAST, FlitType.NORMAL_FLIT,
            'get_nc_dendrites_east_filtin', recv=True, saving_recv=False)

        rslt_west= self._excute_dwnc_command(west_dwnc_list, WEST, FlitType.NORMAL_FLIT,
            'get_nc_dendrites_west_filtin', recv=True, saving_recv=False)
            
        return rslt_east,rslt_west
    
    def get_neuron_inference_status(self, nc_position:tuple,length:int,offset=0) -> tuple[list]:
        """
        获取推理存储器内容
        ---
        Args:
            nc_position: 神经元位置
            length: 读取的字数
            offset (int): 用户指定的地址偏移
            log: 是否输出到控制台
            saving_path: saved path of intermediate results (dwnc, flit in, flit out, etc.)
        Returns: 
            rslt_east,rslt_west
        """
        return self.dump_memory([(nc_position,length,0x0FFFF-offset,True)])
    
    def get_dendrites_memory(self, nc_position:tuple,length:int,offset=0) -> tuple[list]:
        """
        获取树突存储器内容
        ---
        Args:
            nc_position: 神经元位置
            length: 读取的字数
            offset (int): 用户指定的地址偏移
            log: 是否输出到控制台
            saving_path: saved path of intermediate results (dwnc, flit in, flit out, etc.)
        Returns: 
            rslt_east,rslt_west
        """
        return self.dump_memory([(nc_position,length,0x10000+offset,False)])
    
    def get_learn_memory(self, nc_position:tuple,length:int,offset=0) -> tuple[list]:
        """
        获取学习状态存储器内容
        ---
        Args:
            nc_position: 神经元位置
            length: 读取的字数
            offset (int): 用户指定的地址偏移
            log: 是否输出到控制台
            saving_path: saved path of intermediate results (dwnc, flit in, flit out, etc.)
        Returns: 
            rslt_east,rslt_west
        """
        return self.dump_memory([(nc_position,length,0x1DFFF-offset,True)])