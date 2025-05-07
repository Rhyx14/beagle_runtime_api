from .constant import PKG_WRITE
from pathlib import Path
import re
# new part
def _read_and_parse(file:Path,list:list[tuple]) -> None:
    '''
    解析手动编译器的config, 合并数据并保存到list中
    '''
    with open(file,'r') as f:
        raw = f.readlines()

    for _line in raw:
        
        if len(_line)==0 : continue
        if _line[0] == '#' : continue
        _line = _line.split()

        _core_x,_core_y,_waddr=int(_line[2]),int(_line[3]),int(_line[4],16)
        
        if _line[1] == 'write' : 
            list.append((PKG_WRITE,_core_x,_core_y,_waddr,int(_line[5],16)))
        
        elif _line[1] == 'write_ram':
            with open(file.parent / _line[5]) as _f:
                _raw_data= _f.readlines()
            _current_addr=_waddr
            for _2_data_line in _raw_data:
                if len(_2_data_line)==0: continue
                list.append((PKG_WRITE,_core_x,_core_y,_current_addr,int(_2_data_line,16)))
                _current_addr+=1
    

def parse_compiler_config(config_folder,template='*-*-config.dwnc'):
    """
    *-*-config.dwnc => deploy_input.dwnc
    Args:
        deploy_input_dwnc_file (str): 生成的 dwnc 文件的名称
    Returns:
        None
    """
    fwest=[]
    feast=[]
    
    # 将每个神经元的 config 文件整合到整体的 config 文件中
    search_paths = Path.glob(config_folder, template)
    for _search_path in search_paths:
        x = re.findall(r"\d+", _search_path.name)[0]
        _read_and_parse(_search_path, fwest if int(x)<=15 else feast)

    return fwest,feast