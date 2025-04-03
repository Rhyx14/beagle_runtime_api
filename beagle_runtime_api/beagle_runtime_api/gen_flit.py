import struct,random
from .misc import onehot2bin
# 定义flit包长度等的相关常量
FLIT_TEXT_LENGTH_BYTE = 8
FLIT_TEXT_NUM_BYTE = 4
FLIT_TEXT_LENGTH = FLIT_TEXT_NUM_BYTE * (FLIT_TEXT_LENGTH_BYTE + 1)
FLIT_BINARY_LENGTH_VALUE = 4
FLIT_BINARY_NUM_VALUE = 4
FLIT_BINARY_LENGTH = FLIT_BINARY_NUM_VALUE * FLIT_BINARY_LENGTH_VALUE

def gen_flit(item, fin, fbin, direct=0, x_from=-1, y_from=-1, **config_list):
    """
    最里层
    """
    # global last_vc
    # global tick
    # global start_tick
    # global stop_tick
    # global clear_tick
    # global pkg_num
    while config_list.get("config_list") != None:
        config_list = config_list["config_list"]
    if direct == 0:
        config_list["pkg_num"] += 1
    tik = int(item[0])
    cmd = "0xc0000000"
    if item[1] == "cmd":
        cmd = item[2]
    while isinstance(cmd, str):
        cmd = int(cmd,16)
        # cmd = eval(cmd)
    cmd = cmd >> 24
    if (
        tik != config_list["tick"]
        and tik > 0
        and (item[1] != "cmd" or cmd != 0b11011000)
    ):
        cmd = 0b011000
        arg = (tik - config_list["tick"] - 1) & 0xFFFFFF
        cmd_f = 0x3
        if direct == 0:
            l = (cmd_f << 30) + (cmd << 24) + arg
            ss_l = b"%08x\n" % l
            fin.write(ss_l)
            fbin.write(struct.pack("I", l))
        else:
            l = (cmd_f << 30) + (cmd << 24)
            ss_l = b"%08x\n" % l
            for i in range(arg + 1):
                fin.write(ss_l)
                fbin.write(struct.pack("I", l))
    if tik > 0:
        config_list["tick"] = tik
    # vc   = int(item[1])
    vc = 0
    if vc == 0:
        vc = config_list["last_vc"] << 1
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
    config_list["last_vc"] = vc
    op = item[1]
    cmd = "0x80000000"
    if op == "cmd":
        cmd = item[2]
        x = 0
        y = 0
        x_src = 0
        x_dff = 0
        x_sig = 0
        y_src = 0
        y_dff = 0
        y_sig = 0
        if "0xc0000001" in cmd:
            config_list["start_tick"] = tik
        if "0xc0000000" in cmd:
            config_list["stop_tick"] = tik
        if "0xd0000000" in cmd:
            config_list["clear_tick"] = tik
            # if config_list["stop_tick"] == -1 or config_list["clear_tick"] != config_list["stop_tick"]:
            #    print("clear tick must follow stop tick in same step!")
            #    sys.exit(1)
    else:
        x = int(item[2])
        y = int(item[3])
        addr = item[4]
        if len(item) > 5:
            data = item[5]
        else:
            data = 0
        if (
            op == "spike"
            or op == "spike_short"
            or op == "reward"
            or op == "reward_short"
            or op == "write"
            or op == "write_risc"
            or op == "read_ack"
            or op == "read_risc_ack"
            or op == "flow_ack"
            or op == "read"
        ):
            if len(item) > 6:
                x_from = int(item[6])
            if len(item) > 7:
                y_from = int(item[7])
        if op == "flow":
            if len(item) > 5:
                x_from = int(item[5])
            if len(item) > 6:
                y_from = int(item[6])
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
            port = "01000"
        else:
            port = "00010"
    else:
        if y_dff == 0:
            port = "00001"
        elif y_sig == 1:
            port = "00100"
        else:
            port = "10000"
    route_id = y
    if y_from != -1:
        route_id = y_from
    else:
        if y < 0:
            route_id = 0
        elif y > 23:
            route_id = 23
    if op == "read_risc_ack":
        if x_dff == 0:
            x_sig = 1
        if y_dff == 0:
            y_sig = 1
    direct = 2
    cmd_tmp = cmd
    while isinstance(cmd_tmp, str):
        cmd_tmp = int(cmd_tmp,16)
        # cmd_tmp = eval(cmd_tmp)
    pclass = op
    vcnum = (route_id & 0xF) + (direct << 6)
    vcnum2 = direct << 6
    if direct == 1:
        vcnum2 = direct << 6
    # port = eval("0b" + port)
    port = int(port,2)
    port = onehot2bin(port)
    if pclass == "cmd":
        while isinstance(cmd, str):
            cmd = int(cmd,16)
            # cmd = eval(cmd)
        l = cmd
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "write_risc" or pclass == "read_risc_ack":
        while isinstance(addr, str):
            addr = int(addr,16)
            # addr = eval(addr)
        while isinstance(data, str):
            data = int(data,16)
            # data = eval(data)
        if pclass == "read_risc_ack":
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (addr << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data & 0xFFFF0000) >> 1)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data & 0xFFFF) << 15)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "write" or pclass == "read_ack":
        while isinstance(addr, str):
            addr = int(addr,16)
            # addr = eval(addr)
        while isinstance(data, str):
            data = int(data,16)
            # data = eval(data)
        if pclass == "read_ack":
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (addr << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data & 0xFFFFFF000000) >> 21)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data & 0xFFFFFF) << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "read":
        while isinstance(addr, str):
            # addr = int(addr,16)
            addr = eval(eval(addr))
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (addr << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "flow":
        data1 = addr
        while isinstance(data1, str):
            data1 = int(data1,16)
            # data1 = eval(data1)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (data1 << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "flow_ack":
        data1 = addr
        while isinstance(data1, str):
            data1 = int(data1,16)
            # data1 = eval(data1)
        data2 = data
        while isinstance(data2, str):
            data2 = int(data2,16)
            # data2 = eval(data2)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (data1 << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data2 & 0x3FFFFFF8000000) >> 24)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data2 & 0x7FFFFFF) << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "spike":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
        l = (
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "spike_short":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "reward":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "reward_short":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))

def gen_flit_east(
    item, fin, fbin, direct=0, x_from=-1, y_from=-1, **config_list
):
    """
    最里层
    """
    # global last_vc
    # global tick
    # global start_tick
    # global stop_tick
    # global clear_tick
    # global pkg_num
    while config_list.get("config_list") != None:
        config_list = config_list["config_list"]
    if direct == 0:
        config_list["pkg_num"] += 1
    tik = int(item[0])
    cmd = "0xc0000000"
    if item[1] == "cmd":
        cmd = item[2]
    while isinstance(cmd, str):
        cmd = int(cmd,16)
        # cmd = eval(cmd)
    cmd = cmd >> 24
    if (
        tik != config_list["tick"]
        and tik > 0
        and (item[1] != "cmd" or cmd != 0b11011000)
    ):
        cmd = 0b011000
        arg = (tik - config_list["tick"] - 1) & 0xFFFFFF
        cmd_f = 0x3
        if direct == 0:
            l = (cmd_f << 30) + (cmd << 24) + arg
            ss_l = b"%08x\n" % l
            fin.write(ss_l)
            fbin.write(struct.pack("I", l))
        else:
            l = (cmd_f << 30) + (cmd << 24)
            ss_l = b"%08x\n" % l
            for i in range(arg + 1):
                fin.write(ss_l)
                fbin.write(struct.pack("I", l))
    if tik > 0:
        config_list["tick"] = tik
    # vc   = int(item[1])
    vc = 0
    if vc == 0:
        vc = config_list["last_vc"] << 1
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
    config_list["last_vc"] = vc
    op = item[1]
    cmd = "0x80000000"
    if op == "cmd":
        cmd = item[2]
        x = 0
        y = 0
        x_src = 0
        x_dff = 0
        x_sig = 0
        y_src = 0
        y_dff = 0
        y_sig = 0
        if "0xc0000001" in cmd:
            config_list["start_tick"] = tik
        if "0xc0000000" in cmd:
            config_list["stop_tick"] = tik
        if "0xd0000000" in cmd:
            config_list["clear_tick"] = tik
            # if config_list["stop_tick"] == -1 or config_list["clear_tick"] != config_list["stop_tick"]:
            #    print("clear tick must follow stop tick in same step!")
            #    sys.exit(1)
    else:
        x = int(item[2])
        y = int(item[3])
        addr = item[4]
        if len(item) > 5:
            data = item[5]
        else:
            data = 0
        if (
            op == "spike"
            or op == "spike_short"
            or op == "reward"
            or op == "reward_short"
            or op == "write"
            or op == "write_risc"
            or op == "read_ack"
            or op == "read_risc_ack"
            or op == "flow_ack"
            or op == "read"
        ):
            if len(item) > 6:
                x_from = int(item[6])
            if len(item) > 7:
                y_from = int(item[7])
        if op == "flow":
            if len(item) > 5:
                x_from = int(item[5])
            if len(item) > 6:
                y_from = int(item[6])
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
                y_dff = -1 - y
            elif y_src < 0:
                y_src = -y_src
                y_dff = 24 - y
            else:
                y_dff = 0
            if y_src == 16:
                y_src = 15
    if x_dff > 0:
        if x_sig == 1:
            port = "01000"
        else:
            port = "00010"
    else:
        if y_dff == 0:
            port = "00001"
        elif y_sig == 1:
            port = "00100"
        else:
            port = "10000"
    route_id = y
    if y_from != -1:
        route_id = y_from
    else:
        if y < 0:
            route_id = 0
        elif y > 23:
            route_id = 23
    if op == "read_risc_ack":
        if x_dff == 0:
            x_sig = 1
        if y_dff == 0:
            y_sig = 1
    direct = 2
    cmd_tmp = cmd
    while isinstance(cmd_tmp, str):
        cmd_tmp = int(cmd_tmp,16)
        # cmd_tmp = eval(cmd_tmp)
    pclass = op
    vcnum = (route_id & 0xF) + (direct << 6)
    vcnum2 = direct << 6
    if direct == 1:
        vcnum2 = direct << 6
    port = int(port, 2)
    # port = eval("0b" + port)
    port = onehot2bin(port)
    if pclass == "cmd":
        while isinstance(cmd, str):
            cmd = int(cmd,16)
        #     cmd = eval(cmd)
        l = cmd
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "write_risc" or pclass == "read_risc_ack":
        addr = int(addr,16)
        data = int(data,16)
        while isinstance(addr, str):
            addr = int(addr,16)
            # addr = eval(addr)
        while isinstance(data, str):
            data = int(data,16)
            # data = eval(data)
        if pclass == "read_risc_ack":
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (addr << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data & 0xFFFF0000) >> 1)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data & 0xFFFF) << 15)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "write" or pclass == "read_ack":
        while isinstance(addr, str):
            # addr = eval(addr)
            addr = int(addr,16)
        while isinstance(data, str):
            # data = eval(data)
            data = int(data,16)
        if pclass == "read_ack":
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (addr << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data & 0xFFFFFF000000) >> 21)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data & 0xFFFFFF) << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "read":
        while isinstance(addr, str):
            # addr = int(addr,16)
            addr = eval(addr)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (addr << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "flow":
        data1 = addr
        while isinstance(data1, str):
            data1 = int(data1,16)
            # data1 = eval(data1)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (data1 << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "flow_ack":
        data1 = addr
        while isinstance(data1, str):
            data1 = int(data1,16)
            # data1 = eval(data1)
        data2 = data
        while isinstance(data2, str):
            data2 = int(data2,16)
            # data2 = eval(data2)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + (data1 << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x0 << 30) + ((data2 & 0x3FFFFFF8000000) >> 24)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + ((data2 & 0x7FFFFFF) << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "spike":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
        l = (
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "spike_short":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "reward":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
    if pclass == "reward_short":
        dedr_id = addr
        neu_idx = data
        while isinstance(dedr_id, str):
            dedr_id = int(dedr_id,16)
            # dedr_id = eval(dedr_id)
        while isinstance(neu_idx, str):
            neu_idx = int(neu_idx,16)
            # neu_idx = eval(neu_idx)
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
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))
        l = (0x1 << 30) + (dedr_id << 15) + (neu_idx << 3)
        ss_l = b"%08x\n" % l
        fin.write(ss_l)
        fbin.write(struct.pack("I", l))

def gen_flit_parallel(
    x,
    y,
    address,
    value,
    text_buffer,
    text_offset,
    binary_buffer,
    binary_offset,
    **config_list
):
    while config_list.get("config_list") != None:
        config_list = config_list["config_list"]
    src_x = x + 1
    if src_x == 16:
        src_x = 15
    # src_y = 0
    diff_x = x
    # diff_y = 0
    # sign_x = 0
    # sign_y = 0
    if diff_x > 0:
        port = 1
    else:
        port = 0
    route_id = y
    # direct   = 2
    # vcnum    = (route_id & 0xf) + (direct << 6)
    # vcnum2   = (direct << 6)
    # msb      = route_id >> 4
    head = (
        (0x2 << 30)
        + (route_id << 25)
        + (0x1 << 22)
        + (port << 19)
        + (diff_x << 14)
        + (src_x << 5)
    )
    body0 = (0x0 << 30) + (address << 3)
    body1 = (0x0 << 30) + ((value & 0xFFFFFF000000) >> 21)
    tail = (0x1 << 30) + ((value & 0xFFFFFF) << 3)
    text_buffer[text_offset : text_offset + FLIT_TEXT_LENGTH] = (
        b"%08x\n%08x\n%08x\n%08x\n" % (head, body0, body1, tail)
    )
    struct.pack_into("<4I", binary_buffer, binary_offset, head, body0, body1, tail)

def gen_flit_parallel_east(
    x,
    y,
    address,
    value,
    text_buffer,
    text_offset,
    binary_buffer,
    binary_offset,
    **config_list
):
    while config_list.get("config_list") != None:
        config_list = config_list["config_list"]
    src_x = 24 - x
    # if src_x == 16:
    #     src_x = 15
    # src_y = 0
    diff_x = 23 - x
    # diff_y = 0
    sign_x = 1
    # sign_y = 0
    if diff_x > 0:
        port = 3
    else:
        port = 0
    route_id = y
    # direct   = 2
    # vcnum    = (route_id & 0xf) + (direct << 6)
    # vcnum2   = (direct << 6)
    # msb      = route_id >> 4
    head = (
        (0x2 << 30)
        + (route_id << 25)
        + (0x1 << 22)
        + (port << 19)
        + (sign_x << 18)
        + (diff_x << 14)
        + (src_x << 5)
    )
    body0 = (0x0 << 30) + (address << 3)
    body1 = (0x0 << 30) + ((value & 0xFFFFFF000000) >> 21)
    tail = (0x1 << 30) + ((value & 0xFFFFFF) << 3)
    text_buffer[text_offset : text_offset + FLIT_TEXT_LENGTH] = (
        b"%08x\n%08x\n%08x\n%08x\n" % (head, body0, body1, tail)
    )
    struct.pack_into("<4I", binary_buffer, binary_offset, head, body0, body1, tail)