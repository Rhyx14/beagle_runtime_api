import enum
class DWNC(list):
    class COMMAND(enum.Enum):
        CMD=0
        SPIKE=1
        SPIKE_SHORT=2
        REWARD=3
        REWARD_SHORT=4
        WRITE=5
        WRITE_RISC=6
        READ_ACK=7
        READ_RISC_ACK=8
        FLOW_ACK=9
        READ=10
        FLOW=11
    def __init__(self) -> None:
        pass
