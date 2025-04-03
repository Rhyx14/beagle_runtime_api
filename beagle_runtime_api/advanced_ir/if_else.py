from .pseudo_inst import IPseudoInstruction
from darwin3_deployment.ir import DInst,CMP
from .pseudo_inst import jc,jmp,jnc
from .label import Label
from .RREG import RREG
class If(IPseudoInstruction):
    LABEL_ID=0
    @staticmethod
    def get_label_id():
        rslt=f'__label_{If.LABEL_ID}'
        If.LABEL_ID +=1
        return rslt

    def __init__(self,op:str,inline_insts:list=[],Else=[]) -> None:
        _ls=op.split(' ')
        self.rs=_ls[0]
        self.op=_ls[1]
        self.rt=_ls[2]
        
        self.inner_insts=inline_insts
        if len(self.inner_insts)==0:
            raise ValueError(f'If block should have some instructions!')
        self.else_insts=Else
    
    def compile(self) -> list:
        rslt=[]
        if self.op=='==' and self.rt=='0':
            rslt.append(CMP(RREG.R_NAME_MAP[self.rs],RREG.R_NAME_MAP[self.rs],CMP.Func.EQ_0))
        elif self.op=='>=' and self.rt=='0':
            rslt.append(CMP(RREG.R_NAME_MAP[self.rs],RREG.R_NAME_MAP[self.rs],CMP.Func.GE_0))
        elif self.op=='==':
            rslt.append(CMP(RREG.R_NAME_MAP[self.rs],RREG.R_NAME_MAP[self.rt],CMP.Func.EQ))
        elif self.op=='>=':
            rslt.append(CMP(RREG.R_NAME_MAP[self.rs],RREG.R_NAME_MAP[self.rt],CMP.Func.GE))
        else:
            raise ValueError(f'erroneous operator {self.op}')

        rslt.append(jnc(label_if:=If.get_label_id()))
        rslt.extend(compile_instructions(self.inner_insts))
        # rslt[-1]=Label(label_if,rslt[-1],1) # adding label

        if len(self.else_insts)!=0:
            rslt.append(jmp(label_else:=If.get_label_id())) # skip the else-block after if 
            rslt[-1]=Label(label_if,rslt[-1],1) # jump here if not-if
            rslt.extend(compile_instructions(self.else_insts))
            rslt[-1]=Label(label_else,rslt[-1],1) # adding label
        else:
            rslt[-1]=Label(label_if,rslt[-1],1) # jump here if not-if
        return rslt

def compile_instructions(inner_insts):
    rslt_list=[]
    for _2_inst in inner_insts:
        if isinstance(_2_inst,IPseudoInstruction):
            rslt_list.extend(_2_inst.compile())
        else:
            rslt_list.append(_2_inst)
    return rslt_list