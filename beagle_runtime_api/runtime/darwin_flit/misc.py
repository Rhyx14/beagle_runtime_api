from .constant import WEST,EAST,NORTH,SOUTH
def decode_xy_single_board(hd):
    # 单芯片解码
    if hd.dst_y_sign==1: _dst_y= - hd.dst_y
    else: _dst_y=hd.dst_y
    if hd.dst_x_sign==1: _dst_x= - hd.dst_x
    else: _dst_x=hd.dst_x
    match hd.dst_port:
        case 3: # WEST
            _from_y = hd.route_id
            # _from_y = hd.route_id + _dst_y - hd.src_y
            _from_x = hd.src_x + _dst_x -1 # 这里注意是包从路由发送出来dst的值就会-1，所以dst_x是-1核心到目的位置的偏移，而不是0核心。其他方向同理
        # case 1: # EAST
        #     _from_y = hd.route_id + _dst_y - hd.src_y
        #     _from_x = 23 - hd.src_x + _dst_x + 1
        case _:
            raise NotImplementedError(f'dst_port: {hd.dst_port}.')
    return _from_x,_from_y

def encode_xy_single_board(hd,target_x,target_y,via_direction):
    if via_direction == WEST:
        src_x = target_x + 1 # suppose all the pkgs are from x=-1
        src_y = 0

        dst_x = target_x
        dst_x_sign = 0
        
        dst_y = 0
        dst_y_sign = 0

        route_id = target_y
    
    elif via_direction == EAST:
        src_x = 24 - target_x # suppose all the pkgs are from x=24
        src_y = 0

        dst_x = 23 - target_x
        dst_x_sign = 1

        dst_y = 0
        dst_y_sign 

    else:
        raise NotImplementedError
    
    # 确定路由该从哪边走
    if dst_x != 0:
        if dst_x_sign == 1:
            dst_port = 3 # west
        else:
            dst_port = 1 # east
    else: # dst_x == 0
        if dst_y == 0:
            dst_port = 0 # current core
        elif dst_y_sign == 1:
            dst_port = 2 # north
        else:
            dst_port = 4 # south

    hd.src_x=src_x
    hd.src_y=src_y
    hd.dst_x=dst_x
    hd.dst_x_sign=dst_x_sign
    hd.dst_y=dst_y
    hd.dst_y_sign=dst_y_sign
    hd.route_id=route_id
    hd.dst_port=dst_port

    # if op == DWNC.COMMAND.READ_RISC_ACK:
    #     if dst_x == 0:
    #         dst_x_sign = 1
    #     if dst_y == 0:
    #         dst_y_sign = 1