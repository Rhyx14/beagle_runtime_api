from ctypes import LittleEndianStructure,c_int,c_uint

# flit type
class Command(LittleEndianStructure):
    _fields_=[
        ("arg",c_uint,24),
        ("cmd",c_uint,6),
        ("flit_type_head",c_uint,2)
    ]

class Head(LittleEndianStructure):
    _fields_ =[
        ("RA",c_uint,1),
        ("src_y",c_uint,4),
        ("src_x",c_uint,4),
        ("dst_y",c_uint,4),
        ("dst_y_sign",c_uint,1),
        ("dst_x",c_uint,4),
        ("dst_x_sign",c_uint,1),
        ("dst_port",c_uint,3),
        ("pkg_class",c_uint,3),
        ("route_id",c_uint,5),
        ("flit_type_head",c_uint,2),
    ]

class Body0(LittleEndianStructure):
    _fields_=[
        ("reserved",c_uint,3),
        ("waddr",c_uint,17),
        ("RD",c_uint,1),
        ("relay_link",c_uint,6),
        ("relay_id",c_uint,3),
        ("flit_type_body0",c_uint,2),
    ]

class Body1(LittleEndianStructure):
    _fields_=[
        ("reserved",c_uint,3),
        ("wdata1",c_uint,24),
        ("reserved",c_uint,3),
        ("flit_type_body1",c_uint,2),
    ]

class TailRead(LittleEndianStructure):
    _fields_=[
        ("reserved",c_uint,3),
        ("raddr",c_uint,17),
        ("RD",c_uint,1),
        ("relay_link",c_uint,6),
        ("relay_id",c_uint,3),
        ("flit_type_tail",c_uint,2),
    ]

class TailWrite(LittleEndianStructure):
    _fields_=[
        ("reserved",c_uint,3),
        ("wdata0",c_uint,24),
        ("blank",c_uint,3),
        ("flit_type_tail",c_uint,2),
    ]

class TailSpike(LittleEndianStructure):
    _fields_=[
        ("reserved",c_uint,3),
        ("neu_index",c_uint,12),
        ("dedr_id",c_uint,15),
        ("flit_type_tail",c_uint,2),
    ]
