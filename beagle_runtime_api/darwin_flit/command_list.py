from ..dma_direction import WEST
from .encode import encode
class CommandList:
    global_list={}
    __slots__=('_encoded','_cache','_cmd_list','entry')
    def __init__(self,cmd_list:list=None,enable_cache=True,entry=WEST) -> None:
        self._encoded=None
        self._cache=enable_cache
        self._cmd_list=[] if cmd_list is None else cmd_list
        self.entry=entry
        pass

    def append(self,cmd:tuple):
        self._cmd_list.append(cmd)
        self._encoded=None

    def encode(self):
        if self._encoded == None and self._cache:
            rslt=encode(self._cmd_list,self.entry)
            self._encoded = rslt
        return self._encoded
    
    def extend(self,cmd_list):
        if cmd_list.entry != self.entry:
            raise ValueError(f'Two command_lists have different entries: {self.entry} and {cmd_list.entry}')
        self._cmd_list.extend(cmd_list._cmd_list)

        if self._cache:
            if self._encoded!=None and cmd_list._encode!=None: 
                self._encoded += cmd_list._encode
            else:
                self._encoded=None
    
    def save(self,path):
        with open(path,'w') as f:
            if self._encoded !=None:
                for i in range(0, len(self._encoded), 4):
                    # 获取当前行的4个字节（不足4字节用0填充）
                    chunk = self._encoded[i:i+4]
                    # 小尾格式：逆序处理字节
                    little_endian_bytes = chunk[::-1]
                    f.write(little_endian_bytes.hex())
                    f.write("\n")
            else:
                for _cmd in self._cmd_list:
                    f.write(str(_cmd))
                    f.write("\n")

    def __getitem__(self,index):
        return self._cmd_list[index]
    
    def __iter__(self):
        return iter(self._cmd_list)
    
    def __len__(self):
        return len(self._cmd_list)