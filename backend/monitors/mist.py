from monitors.aldx import AldxMonitor

class MistMonitor(AldxMonitor):
    def __init__(self,
                 symbol = "MIST",
                 press_release_url = "https://investors.milestonepharma.com/press-releases",
                 ):
        super().__init__(symbol, press_release_url)
