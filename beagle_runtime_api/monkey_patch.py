import torch
from functools import reduce
from loguru import logger
try:
    from darwin3_runtime_api.darwin3_device import darwin3_device as old_api_device
    logger.info('detect darwin3_runtime_api installed, patching new api')
    def run_with_torch_tensor(self,spike_tensor,output_layer_name,expect_output_shape:tuple,extra_time_steps=0,saving_input=False,saving_recv=False,print_log=False,clear_state=False):
        """
        接收应用给的 PyTorch Tensor
        Args:
            spike_tensor: in [t x], 注意batch_size必须为1
        Returns:
            result tensor: in [t x] 本次运行结束时硬件返回给应用的脉冲
        """
        if len(spike_tensor.shape)>2:
            spike_tensor=spike_tensor.flatten(1).cpu()

        time_step=spike_tensor.shape[0]

        spike_list=[]
        for _i in range(time_step):
            spike_list.append(torch.where(spike_tensor[_i]==1)[0].tolist())

        for _ in range(extra_time_steps): spike_list.append([])

        rslt = self.run_darwin3_withfile(spike_neurons=spike_list)

        target_t = expect_output_shape[0]
        target_x = reduce(lambda x,y : x*y, expect_output_shape[1:],1)
        # target_t,target_x=expect_output_shape
        output_spike=torch.zeros(target_t,target_x)
        rslt=rslt[-target_t:]
        for _t,_o in enumerate(rslt):
            if len(_o)==0: continue
            _ls=[_2_o for _,_2_o in _o]
            output_spike[_t,torch.tensor(_ls)]=1
        return output_spike.view(*expect_output_shape)
    old_api_device.run_with_torch_tensor=run_with_torch_tensor

    def reset_freq(self,freq=333):
        """
        复位硬件接口相关逻辑和硬件系统(darwin3 芯片, DMA 等)
        Args: 
            None
        Returns:
            None
        """
        self.__transmit_flit__(port=self.port[0], data_type=old_api_device.CHIP_RESET)
        self.__transmit_flit__(port=self.port[0], data_type=old_api_device.SET_FREQUENCY, freq=freq)
        print("Please check the information on the Darwin3 development board to determine if the configuration was successful.")
        return
    old_api_device.reset_freq=reset_freq

except ImportError:
    pass