from pathlib import Path
import json,re,os
from .darwin_flit.constant import PKG_WRITE,WEST,EAST
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
        
        # # config_neuron_list (list): 需要进行配置的神经元列表
        # self.config_neuron_coord_list=[]

        # search_paths = Path.glob(self.model_path, "*-*-config.dwnc")

        # self.isreset = {}
        # self.vtreset = {}
        # for search_path in search_paths:
        #     file = search_path.name
        #     _neuron_coord = re.findall(r"\d+", file)
        #     _neuron_coord = (int(_neuron_coord[0]),int(_neuron_coord[1]))
        #     self.config_neuron_coord_list.append(_neuron_coord)
        #     with open(self.model_path / file,'r') as f:
        #         l = f.readlines()
        #         index = len(l)-1
        #         flag2 = False
        #         flag1 = False
        #         while index>=0:
        #             temp = l[index].split()
        #             if len(temp)>=6 and 'is' in temp[5]:
        #                 self.isreset[_neuron_coord] = l[index]
        #                 flag1 = True
        #             elif len(temp)>=6 and 'vt' in temp[5]:
        #                 self.vtreset[_neuron_coord] = l[index]
        #                 flag2 = True
        #             if flag1 and flag2:
        #                 break
        #             index -= 1

        # # deploy_from_east (bool): 判断是否需要从东边进行配置
        # self.deploy_from_east = False

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

# # new part
# def read_and_parse(file:Path,list:list[tuple]) -> None:
#     '''
#     解析手动编译器的config, 合并数据并保存到list中
#     '''
#     with open(file,'r') as f:
#         raw = f.readlines()

#     for _line in raw:
        
#         if len(_line)==0 : continue
#         if _line[0] == '#' : continue
#         _line = _line.split()

#         _core_x,_core_y,_waddr=int(_line[2]),int(_line[3]),int(_line[4],16)
        
#         if _line[1] == 'write' : 
#             list.append((PKG_WRITE,_core_x,_core_y,_waddr,int(_line[5],16)))
        
#         elif _line[1] == 'write_ram':
#             with open(file.parent / _line[5]) as _f:
#                 _raw_data= _f.readlines()
#             _current_addr=_waddr
#             for _2_data_line in _raw_data:
#                 if len(_2_data_line)==0: continue
#                 list.append((PKG_WRITE,_core_x,_core_y,_current_addr,int(_2_data_line,16)))
#                 _current_addr+=1
    

# def parse_compiler_config(config_folder,template='*-*-config.dwnc'):
#     """
#     *-*-config.dwnc => deploy_input.dwnc
#     Args:
#         deploy_input_dwnc_file (str): 生成的 dwnc 文件的名称
#     Returns:
#         None
#     """
#     fwest=[]
#     feast=[]
    
#     # 将每个神经元的 config 文件整合到整体的 config 文件中
#     search_paths = Path.glob(config_folder, template)
#     for _search_path in search_paths:
#         x = re.findall(r"\d+", _search_path.name)[0]
#         read_and_parse(_search_path, fwest if int(x)<=15 else feast)

#     return fwest,feast