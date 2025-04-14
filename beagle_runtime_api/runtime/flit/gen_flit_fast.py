import struct,random
from .misc import onehot2bin
from .flit_constant import FLIT_BINARY_LENGTH,FLIT_BINARY_LENGTH_VALUE,FLIT_TEXT_LENGTH,FLIT_BINARY_NUM_VALUE,FLIT_TEXT_LENGTH_BYTE,FLIT_TEXT_NUM_BYTE
from .flit_gen_status import FlitGenStatus
from ..dwnc import DWNC
def gen_flit_mem_west(dwnc:tuple, fbin, direct, x_from, y_from, flit_gen_status:FlitGenStatus):
    """
    dwnc -> flit
    """
    
    if direct == 0:
        flit_gen_status.pkg_num += 1
    tik = dwnc[0]
    
    cmd = 0xc0000000
    if dwnc[1] == DWNC.COMMAND.CMD: # if cmd, next one is the command 
        cmd = dwnc[2]
    cmd = cmd >> 24

    if (
        tik != flit_gen_status.tick
        and tik > 0
        and (dwnc[1] != DWNC.COMMAND.CMD or cmd != 0b11011000)
    ):
        cmd = 0b011000
        arg = (tik - flit_gen_status.tick - 1) & 0xFFFFFF
        cmd_f = 0x3
        if direct == 0:
            l = (cmd_f << 30) + (cmd << 24) + arg
            fbin.write(struct.pack("I", l))
        else:
            l = (cmd_f << 30) + (cmd << 24)
            for i in range(arg + 1):
                fbin.write(struct.pack("I", l))
    if tik > 0:
        flit_gen_status.tick = tik
    # vc   = int(item[1])
    vc = 0
    if vc == 0:
        vc = flit_gen_status.last_vc << 1
        if vc > 8:
            vc = 1
    elif vc not in (1, 2, 4, 8):
        vc_list = []
        if vc & 0x1:
            vc_list.append(1)
        if vc & 0x2:
            vc_list.append(2)
        if vc & 0x4:
            vc_list.append(4)
        if vc & 0x8:
            vc_list.append(8)
        vc = random.choice(vc_list)
    flit_gen_status.last_vc = vc

    op = dwnc[1]
    cmd = 0x80000000
    if op == DWNC.COMMAND.CMD:
        cmd = dwnc[2]
        x = 0
        y = 0
        x_src = 0
        x_dff = 0
        x_sig = 0
        y_src = 0
        y_dff = 0
        y_sig = 0
        if cmd == 0xc0000001:
            flit_gen_status.start_tick = tik
        elif cmd == 0xc0000000:
            flit_gen_status.stop_tick = tik
        elif cmd == 0xd0000000:
            flit_gen_status.clear_tick = tik
            # if config_list["stop_tick"] == -1 or config_list["clear_tick"] != config_list["stop_tick"]:
            #    print("clear tick must follow stop tick in same step!")
            #    sys.exit(1)
    else:
        x = dwnc[2]
        y = dwnc[3]
        addr = dwnc[4]
        if len(dwnc) > 5:
            data = dwnc[5]
        else:
            data = 0
        if (
            op == DWNC.COMMAND.SPIKE
            or op == DWNC.COMMAND.SPIKE_SHORT
            or op == DWNC.COMMAND.REWARD# "reward"
            or op == DWNC.COMMAND.REWARD_SHORT#"reward_short"
            or op == DWNC.COMMAND.WRITE#"write"
            or op == DWNC.COMMAND.WRITE_RISC#"write_risc"
            or op == DWNC.COMMAND.READ_ACK#"read_ack"
            or op == DWNC.COMMAND.READ_RISC_ACK#"read_risc_ack"
            or op == DWNC.COMMAND.FLOW_ACK#"flow_ack"
            or op == DWNC.COMMAND.READ#"read"
        ):
            if len(dwnc) > 6:
                x_from = dwnc[6]
            if len(dwnc) > 7:
                y_from = dwnc[7]
        if op == DWNC.COMMAND.FLOW:
            if len(dwnc) > 5:
                x_from = dwnc[5]
            if len(dwnc) > 6:
                y_from = dwnc[6]
        x_src = x_from - x
        if x_src > 0:
            x_sig = 1
        else:
            x_src = -x_src
            x_sig = 0
        if y_from != -1 and x_from != -1:
            if x_src != 0:
                if x_sig == 1:
                    x_dff = -1 - x
                else:
                    x_dff = 24 - x
            else:
                x_dff = 0
        elif x_src >= 1:
            x_dff = x_src - 1
        else:
            x_dff = 0
        if x_src == 16:
            x_src = 15
        if y_from == -1:
            if y < 0:
                y_sig = 1
                y_dff = -y - 1
                y_src = -y
            elif y < 24:
                y_sig = 0
                y_dff = 0
                y_src = 0
            else:
                y_sig = 0
                y_dff = y - 24
                y_src = y - 23
        else:
            y_sig = 0
            y_src = y_from - y
            if y_src > 0:
                y_sig = 1
                y_dff = y_from - y
            elif y_src < 0:
                y_src = -y_src
                y_dff = y - y_from
            else:
                y_dff = 0
            if y_src == 16:
                y_src = 15
    if x_dff > 0:
        if x_sig == 1:
            port = 3 #"01000"
            # port= 
        else:
            port = 1 # "00010"
    else:
        if y_dff == 0:
            port = 0 #"00001"
        elif y_sig == 1:
            port = 3 # "00100"
        else:
            port = 4 #"10000"
    route_id = y
    if y_from != -1:
        route_id = y_from
    else:
        if y < 0:
            route_id = 0
        elif y > 23:
            route_id = 23
    if op == DWNC.COMMAND.READ_RISC_ACK:
        if x_dff == 0:
            x_sig = 1
        if y_dff == 0:
            y_sig = 1
    direct = 2

    # vcnum = (route_id & 0xF) + (direct << 6)
    # vcnum2 = direct << 6
    # if direct == 1:
    #     vcnum2 = direct << 6

    if op == DWNC.COMMAND.SPIKE:
        dedr_id = addr
        neu_idx = data
        l1 = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x0 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        l2 = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        fbin.write(struct.pack("II", l1,l2))

    elif op == DWNC.COMMAND.SPIKE_SHORT:
        dedr_id = addr
        neu_idx = data
        l = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x4 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        fbin.write(struct.pack("I", l))

    elif op == DWNC.COMMAND.CMD:
        fbin.write(struct.pack("I", cmd))

    elif op == DWNC.COMMAND.WRITE or op == DWNC.COMMAND.READ_ACK:
        if op == DWNC.COMMAND.READ_ACK:
            l1 = (
                (0x2 << 30)
                + (route_id << 25)
                + (0x1 << 22)
                + (port << 19)
                + (x_sig << 18)
                + (x_dff << 14)
                + (y_sig << 13)
                + (y_dff << 9)
                + (x_src << 5)
                + (y_src << 1)
                + (1 << 0)
            )
        else:
            l1 = (
                (0x2 << 30)
                + (route_id << 25)
                + (0x1 << 22)
                + (port << 19)
                + (x_sig << 18)
                + (x_dff << 14)
                + (y_sig << 13)
                + (y_dff << 9)
                + (x_src << 5)
                + (y_src << 1)
            )
        l2 = (0x0 << 30) + (addr << 3)
        l3 = (0x0 << 30) + ((data & 0xFFFFFF000000) >> 21)
        l4 = (0x1 << 30) + ((data & 0xFFFFFF) << 3)

        fbin.write(struct.pack("IIII",l1,l2,l3,l4))

    elif op == DWNC.COMMAND.READ:
        l = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x2 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (addr << 3)
        fbin.write(struct.pack("I", l))

    elif op == DWNC.COMMAND.WRITE_RISC or op == DWNC.COMMAND.READ_RISC_ACK:
        if op == DWNC.COMMAND.READ_RISC_ACK:
            l = (
                (0x2 << 30)
                + (route_id << 25)
                + (0x1 << 22)
                + (port << 19)
                + (x_sig << 18)
                + (x_dff << 14)
                + (y_sig << 13)
                + (y_dff << 9)
                + (x_src << 5)
                + (y_src << 1)
                + (1 << 0)
            )
        else:
            l = (
                (0x2 << 30)
                + (route_id << 25)
                + (0x1 << 22)
                + (port << 19)
                + (x_sig << 18)
                + (x_dff << 14)
                + (y_sig << 13)
                + (y_dff << 9)
                + (x_src << 5)
                + (y_src << 1)
            )
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (addr << 3)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data & 0xFFFF0000) >> 1)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data & 0xFFFF) << 15)
        fbin.write(struct.pack("I", l))

    elif op == DWNC.COMMAND.FLOW:
        data1 = addr
        l = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x3 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (data1 << 3)
        fbin.write(struct.pack("I", l))

    elif op == DWNC.COMMAND.FLOW_ACK:
        data1 = addr
        data2 = data
        l = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x7 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (data1 << 3)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data2 & 0x3FFFFFF8000000) >> 24)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data2 & 0x7FFFFFF) << 3)
        fbin.write(struct.pack("I", l))

    elif op == DWNC.COMMAND.REWARD:
        dedr_id = addr
        neu_idx = data
        l = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x5 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        fbin.write(struct.pack("I", l))

    elif op == DWNC.COMMAND.REWARD_SHORT:
        dedr_id = addr
        neu_idx = data
        l = (
            (0x2 << 30)
            + (route_id << 25)
            + (0x6 << 22)
            + (port << 19)
            + (x_sig << 18)
            + (x_dff << 14)
            + (y_sig << 13)
            + (y_dff << 9)
            + (x_src << 5)
            + (y_src << 1)
        )
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        fbin.write(struct.pack("I", l))

    else:
        raise ValueError()
