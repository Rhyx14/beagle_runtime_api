class FlitGenStatus:
    __slots__=(
        "last_vc",
        "tick",
        "start_tick",
        "stop_tick",
        "clear_tick",
        "pkg_num")
    def __init__(self,last_vc,tick,start_tick,stop_tick,clear_tick,pkg_num) -> None:
        self.last_vc=last_vc
        self.tick=tick
        self.start_tick=start_tick
        self.stop_tick=stop_tick
        self.clear_tick=clear_tick
        self.pkg_num=pkg_num
        pass
