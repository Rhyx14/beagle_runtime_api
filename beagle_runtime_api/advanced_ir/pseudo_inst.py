from darwin3_deployment.ir import JC,SUB,ADDI
from .label import LabledInstructionBase

class IPseudoInstruction():
    def compile(self) -> list:
        raise NotImplementedError
 
class jnc(LabledInstructionBase,IPseudoInstruction):
    '''
    jump if the condition is unmet
    '''
    def compile(self) -> list:
        if self.addr is not None: return [JC(1,1,self.addr)]
        else: return []

class jc(LabledInstructionBase,IPseudoInstruction):
    '''
    jump if the condition is met
    '''
    def compile(self) -> list:
        if self.addr is not None: return [JC(1,0,self.addr)]
        else: return []

class jmp(LabledInstructionBase,IPseudoInstruction):
    '''
    jump whatever the condition is
    '''
    def compile(self) -> list:
        if self.addr is not None: return [JC(0,0,self.addr)]
        else: return []

class set_value(IPseudoInstruction):
    '''
    Assign value for a given register.
    '''
    def __init__(self,reg,imme) -> None:
        super().__init__()
        self.reg=reg
        self.imme=imme
    def compile(self) -> list:
        return [
            SUB(self.reg,self.reg),
            ADDI(self.reg,self.imme)
        ]
