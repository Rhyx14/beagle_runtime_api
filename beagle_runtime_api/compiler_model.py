from pathlib import Path
import json,re,os
from .darwin_flit.constant import PKG_WRITE
from .dma_direction import WEST,NORTH,SOUTH,EAST
from .darwin_flit.command_list import CommandList
class CompilerModel():
    def _load_write_ram(self,file,x,y,start_addr,entry):
        rslt=CommandList(entry=entry)
        with open(file,'r') as f:
            lines=f.readlines()
        current_addr=start_addr
        for _data_line in lines:
            if len(_data_line) ==0 : continue
            rslt.append((PKG_WRITE,x,y,current_addr,int(_data_line,16)))
            current_addr+=1
        return rslt

    def __init__(self,model_path:str | Path) -> None:
        self.model_path=Path(model_path)

        # input_neuron (list): 读取 input_neuron.json 文件, 存储为list
        with open(self.model_path / "input_neuron.json", "r") as f:
            self.input_neuron = json.load(f)

        self.used_neuron_cores={}
        self.clear_is_west=CommandList(entry=WEST)
        self.clear_is_east=CommandList(entry=EAST)

        # 配置nc信息和clear_state 信息
        search_paths = Path.glob(self.model_path, "*-*-config.dwnc")
        for search_path in search_paths:
            file = search_path.name
            _neuron_coord = re.findall(r"\d+", file)
            _neuron_coord = (int(_neuron_coord[0]),int(_neuron_coord[1]))
            
            if _neuron_coord[0]<=15: _deploy_cmd_list=CommandList(entry=WEST)
            else:                    _deploy_cmd_list=CommandList(entry=EAST)

            with open(self.model_path / file,'r') as f:
                _lines=f.readlines()
            for _2_line in _lines:
                if len(_2_line)==0 or _2_line[0] == '#' : continue
                _2_line = _2_line.split()

                _2_x,_2_y,_2_waddr=int(_2_line[2]),int(_2_line[3]),int(_2_line[4],16)

                if _2_line[1] == 'write' : 
                    _deploy_cmd_list.append((PKG_WRITE,_2_x,_2_y,_2_waddr,int(_2_line[5],16)))

                elif _2_line[1] == 'write_ram':
                    _2_cmd_list=self._load_write_ram(self.model_path / _2_line[5],_2_x,_2_y,_2_waddr,_deploy_cmd_list.entry)
                    # store the is state 
                    if _2_line[5].find('is')!=-1:
                        if _deploy_cmd_list.entry==WEST: self.clear_is_west.extend(_2_cmd_list)
                        if _deploy_cmd_list.entry==EAST: self.clear_is_east.extend(_2_cmd_list)

                    _deploy_cmd_list.extend(_2_cmd_list)

            self.used_neuron_cores[_neuron_coord]=_deploy_cmd_list

        # 配置output索引
        format = "output_neuron*.json"
        pattern = re.compile(r'output_neuron_(.*?)\.json')
        search_paths = Path.glob(self.model_path , format)
        self.output_neuron_info_jsons={}
        for search_path in search_paths:
            file = search_path.name
            output_name = pattern.match(file).group(1)
            with open(self.model_path / file, "r") as f:
                _js=json.load(f)
                _new_json={}
                for _2_x,_2_id in _js.items():
                    _3_s=_2_x.split(',')
                    _new_json[(int(_3_s[0]),int(_3_s[1]),int(_3_s[2]))]=_2_id
                self.output_neuron_info_jsons[output_name]=_new_json

        if os.path.exists(self.model_path / "delay_record.json"):
            with open(self.model_path / "delay_record.json", "r") as f:
                self.delay_neuron = json.load(f)
        else:
            self.delay_neuron = {}
        
        pass