from darwin3_deployment.ir import DInst
class Label():
    def __init__(self,label_name,instruction:DInst,offset=0) -> None:
        self.label_name=label_name
        self.instruction=instruction
        self.offset=offset

class LabledInstructionBase():
    def __init__(self,label,addr=None) -> None:
        self.label=label
        self.addr=addr
    def process_label(self,label_addr_dict) -> DInst:
        self.addr=label_addr_dict[self.label]
