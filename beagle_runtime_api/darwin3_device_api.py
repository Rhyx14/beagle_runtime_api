import shutil, logging
from pathlib import Path
from functools import reduce

from .compiler_model import CompilerModel

from .darwin_flit.result import SpikeResult, MemResult
from .darwin_flit.constant import PKG_WRITE,PKG_WRITE,PKG_SPIKE,PKG_CMD,PKG_READ,WEST,EAST
from .darwin_flit.command_list import CommandList
from .darwin3_device_func import FlitType
try: 
    import torch
except ImportError as e:
    print('PyTorch is not installed, ensure that no torch-API is used!')

from .deprecated import deprecated
from .darwin3_device_func import gen_spike_input_dwnc,transmit_flit,gen_deploy_flitin,excute_dwnc_command, excute_dwnc_command_prof

class darwin3_device(object):
    """
    用于和Darwin3开发板进行通信的类
    """

    def __init__(
        self, 
        ip: str | tuple | list =['172.31.111.35'], 
        port=[6000, 6001], 
        step_size=100000, 
        app_path:Path | str="../", 
        log_debug=False, 
        **kwds,
    ):
        """
        Args:
            ip :              Darwin3 板卡设备 ip, [list | tuple] 为兼容api格式，不起作用
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

        # ip (str): 和 Darwin3 进行 TCP 连接的 IP 地址
        # port (list(int)): 和 Darwin3 进行 TCP 连接的端口号序列
        if isinstance(ip,(list,tuple)):
            ip=ip[0]
        self.ip = ip
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
        transmit_flit(self.ip,port=self.port[0], data_type=FlitType.CHIP_RESET)
        transmit_flit(self.ip,port=self.port[0], data_type=FlitType.SET_FREQUENCY)
        print("[INFO] Reset chip complete, please check the output on the Darwin3 development board.")

    @deprecated("此方法同darwin3_init()为旧版兼容API, 请使用 reset_freq(), 包含了reset和设置频率组合")
    def reset(self,freq=333):
        """
        复位硬件接口相关逻辑和硬件系统(darwin3 芯片, DMA 等)
        Args: 
            None
        Returns:
            None
        """
        transmit_flit(self.ip,port=self.port[0], data_type=FlitType.CHIP_RESET)
        print("[INFO] Please check the output on the Darwin3 development board.")
        return
    
    @deprecated("此方法同reset()为旧版兼容API, 请使用 reset_freq(), 包含了reset和设置频率组合")
    def darwin3_init(self, freq=333):
        """
        按照指定频率配置 darwin3 芯片。
        Args:
            freq (int): 兼容参数，无实际作用
        Returns:
            None
        """
        transmit_flit(self.ip,port=self.port[0], data_type=FlitType.SET_FREQUENCY)
        print("[INFO] Please check the output on the Darwin3 development board.")
        return
    
    @deprecated("此方法为旧版兼容API, 请使用 run_darwin3_with_spikes")
    def run_darwin3_withoutfile(self,spike_neurons):
        '''
        '''
        return self.run_darwin3_with_spikes(spike_neurons)

    @deprecated("此方法为旧版兼容API, 请使用 run_darwin3_with_spikes")
    def run_darwin3_withfile(self,spike_neurons):
        '''
        '''
        return self.run_darwin3_with_spikes(spike_neurons)
        
    def clear_vth_only(self, ISC=False, LSC=False, clear=True, dwnc_file=None):
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

        excute_dwnc_command(self,west_dwnc_list,WEST,FlitType.NORMAL_FLIT,'cls_west',recv=False,saving_recv=False)
        excute_dwnc_command(self,east_dwnc_list,EAST,FlitType.NORMAL_FLIT,'cls_east',recv=False,saving_recv=False)

        return
            
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

        excute_dwnc_command(self,west_dwnc_list,WEST,FlitType.NORMAL_FLIT,'cls_west',recv=False,saving_recv=False)
        excute_dwnc_command(self,east_dwnc_list,EAST,FlitType.NORMAL_FLIT,'cls_east',recv=False,saving_recv=False)

        return
    
    def set_hardware_stepsize(self,hardware_stepsize):
        '''
        set hardware stepsize (cycles)
        '''
        self._hardware_step_size=hardware_stepsize
        west_dwnc_list=CommandList([(PKG_CMD,0,1)],entry=WEST)
        east_dwnc_list=CommandList([(PKG_CMD,0,1)],entry=EAST)
        west_dwnc_list.append((PKG_CMD,0b100000,self._hardware_step_size))
        west_dwnc_list.append((PKG_CMD,0b100000,self._hardware_step_size))
        west_dwnc_list.append((PKG_CMD,0,0))
        east_dwnc_list.append((PKG_CMD,0,0))
        excute_dwnc_command(self,west_dwnc_list,WEST,FlitType.NORMAL_FLIT,'',recv=False)
        excute_dwnc_command(self,east_dwnc_list,EAST,FlitType.NORMAL_FLIT,'',recv=False)
        return

    def deploy_config(self,save=False):
        """
        在部署芯片上部署并使能相关核心, 同时清除神经元的相关状态
        Args:
            None
        Returns:
            None
        """
        dwnc_west,dwnc_east=gen_deploy_flitin(self.model,self._hardware_step_size)
        if save:
            dwnc_west.encode()
            dwnc_west.save(self._cache_path / 'deploy_west.txt')
            dwnc_east.encode()
            dwnc_east.save(self._cache_path/ 'deploy_east.txt')
        excute_dwnc_command(self,dwnc_west,WEST,FlitType.NORMAL_FLIT,'deploy_west',recv=True)
        excute_dwnc_command(self,dwnc_east,EAST,FlitType.NORMAL_FLIT,'deploy_east',recv=True)

    def run_darwin3_with_spikes(self, spike_list: list,saving_input=False,saving_recv=False):
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
        dwnc_list=gen_spike_input_dwnc(self.model.input_neuron,spike_list)
        if saving_input:
            dwnc_list.encode()
            dwnc_list.save(self._cache_path / 'run_input_dwnc.txt')

        max_tik_index,rslt=excute_dwnc_command(self,
            dwnc_list,
            WEST,
            FlitType.NORMAL_FLIT,
            'run_flitin',
            True,
            saving_recv)

        return SpikeResult.parse_spike(self.model.output_neuron_info_jsons,rslt,max_tik_index+1)
    
    def run_with_torch_tensor(self,spike_tensor,output_layer_name,expect_output_shape:tuple,extra_time_steps=0,saving_input=False,saving_recv=False,clear_state=False):
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
        dwnc_list=gen_spike_input_dwnc(self.model.input_neuron,spike_list)
        if saving_input:
            (self._cache_path / 'run_input_dwnc.txt').write_text('\n'.join(dwnc_list))

        max_tik_index,rslt=excute_dwnc_command(self,
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
    
    def run_with_torch_tensor_prof(self,secretary,spike_tensor,output_layer_name,expect_output_shape:tuple,extra_time_steps=0,saving_input=False,saving_recv=False,clear_state=False):
        """
        接收应用给的 PyTorch Tensor
        Args:
            spike_tensor: in [t x], 注意batch_size必须为1
        Returns:
            result tensor: in [t x] 本次运行结束时硬件返回给应用的脉冲
        """
        with secretary.flame_time('tensor to spikes'):
            if len(spike_tensor.shape) >2:
                spike_tensor=spike_tensor.flatten(1)
            t,_=spike_tensor.shape
            spike_list=[]
            for _i in range(t):
                spike_list.append(torch.where(spike_tensor[_i]==1)[0].tolist())

            for _ in range(extra_time_steps): spike_list.append([])

        # 生成spike的dwnc
        with secretary.flame_time('spikes to flit'):
            dwnc_list=gen_spike_input_dwnc(self.model.input_neuron,spike_list)
            if saving_input:
                (self._cache_path / 'run_input_dwnc.txt').write_text('\n'.join(dwnc_list))
        with secretary.flame_time('send flit'):
            max_tik_index,rslt=excute_dwnc_command_prof(self,
                secretary,
                dwnc_list,
                WEST,
                FlitType.RESET_SPIKING_INPUT if clear_state else FlitType.NORMAL_FLIT,
                'run_flitin',
                True,
                saving_recv)            

        with secretary.flame_time('flit to spikes'):
            rslt=SpikeResult.parse_spike_single_layer(self.model.output_neuron_info_jsons[output_layer_name],rslt,max_tik_index+1)
        
        with secretary.flame_time('spikes to tensor'):
            target_t = expect_output_shape[0]
            target_x = reduce(lambda x,y : x*y, expect_output_shape[1:],1)
            # target_t,target_x=expect_output_shape
            output_spike=torch.zeros(target_t,target_x)
            rslt=rslt[-target_t:]
            for _t,_spike_ids in enumerate(rslt):
                if len(_spike_ids)==0: continue
                output_spike[_t,torch.tensor(_spike_ids)]=1
        
        return output_spike.view(*expect_output_shape)

    def clear_neurons_states_prof(self,secretary, ISC=False, LSC=False, clear=True, dwnc_file=None):
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
            
        with secretary.flame_time('re-init model'):
            excute_dwnc_command_prof(self,secretary,west_dwnc_list,WEST,FlitType.NORMAL_FLIT,'cls_west',recv=False,saving_recv=False)
            excute_dwnc_command_prof(self,secretary,east_dwnc_list,EAST,FlitType.NORMAL_FLIT,'cls_east',recv=False,saving_recv=False)

        return

    def dump_memory(self,dump_request:list[tuple],special_format='',**kwds) -> tuple[list]:
        '''
        dump the memory of the specific neuromorphic core.
        ---
        @dump_request: 
        
            list of tuple:(

                nc_position: nc core coordinate, (x,y)

                length : words to be read, int

                offset : words offset, int

            )

        @special_format: (weight | '') decode in special format
                    weight: format results as kwds['bit_width'] bitwidth weight (default 8-bit)
        '''
        # raise NotImplementedError
        # construct dwnc list
        west_dwnc_list=CommandList(entry=WEST)
        east_dwnc_list=CommandList(entry=EAST)

        west_dwnc_list.append((PKG_CMD,0,1))
        east_dwnc_list.append((PKG_CMD,0,1))
        # x,y=nc_position
        for (_x,_y), _length, _offset in dump_request:
            for _2_addr in range(_offset, _offset+_length):
                _cmd=(PKG_READ,_x,_y,_2_addr)
                if _x>=15:
                    east_dwnc_list.append(_cmd)
                else:
                    west_dwnc_list.append(_cmd)

        west_dwnc_list.append((PKG_CMD,0,0))
        east_dwnc_list.append((PKG_CMD,0,0))
        
        _,rslt_east= excute_dwnc_command(self,east_dwnc_list,EAST, FlitType.NORMAL_FLIT,
            'get_nc_dendrites_east_filtin', recv=True, saving_recv=False)

        _,rslt_west= excute_dwnc_command(self,west_dwnc_list, WEST, FlitType.NORMAL_FLIT,
            'get_nc_dendrites_west_filtin', recv=True, saving_recv=False)
        
        if special_format == 'weight':
            if 'bit_width' in kwds: bit=8
            else: bit =8
            return MemResult.parse_weight(rslt_west,bit),MemResult.parse_weight(rslt_east,bit)
        else:
            return MemResult.parse_memory(rslt_west),MemResult.parse_memory(rslt_east)
    
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

    def set_memory(self,reg_list):
        '''
        设置神经元核心存储值
        ---
        @reg_list: list of tuple:(

            nc_position: nc core coordinate, (x,y)

            reg_addr: register address, int

            reg_value: register value, int

        )
        '''
        west_dwnc_list=CommandList(entry=WEST)
        east_dwnc_list=CommandList(entry=EAST)

        west_dwnc_list.append((PKG_CMD,0,1))
        east_dwnc_list.append((PKG_CMD,0,1))
        for (_x,_y), _reg_addr, _reg_value in reg_list:
            _cmd=(PKG_WRITE,_x,_y,_reg_addr,_reg_value)
            if _x>=15:
                east_dwnc_list.append(_cmd)
            else:
                west_dwnc_list.append(_cmd)

        west_dwnc_list.append((PKG_CMD,0,0))
        east_dwnc_list.append((PKG_CMD,0,0))

        excute_dwnc_command(self,west_dwnc_list,WEST,FlitType.NORMAL_FLIT,'set_memory',recv=False,saving_recv=False)
        excute_dwnc_command(self,east_dwnc_list,EAST,FlitType.NORMAL_FLIT,'set_memory',recv=False,saving_recv=False)

        return