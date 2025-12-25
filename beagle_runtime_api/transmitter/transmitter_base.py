from pathlib import Path
class TransmitterBase():
    def __init__(self):
        pass
    
    def send_flit(self, 
                  direction,
                  data_type,
                  flit_bin:bytearray,
                  recv_flag:bool,
                  recv_run_flit_file:Path
                  ):
        raise NotImplementedError