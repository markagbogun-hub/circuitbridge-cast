"""Non-destructive timeline model used by the v2 workstation UI."""
from dataclasses import dataclass
from typing import List

@dataclass
class TimelineMarker:
    time: float
    kind: str
    duration: float
    message: str = ""

class Timeline:
    def __init__(self,duration=0.0):
        self.duration=float(duration)
        self.position=0.0
        self.selection=(0.0,0.0)
        self.markers: List[TimelineMarker]=[]

    def seek(self,seconds):
        self.position=max(0.0,min(float(seconds),self.duration))

    def select(self,start,end):
        self.selection=(max(0.0,min(start,self.duration)),
                        max(0.0,min(end,self.duration)))

    def clear_selection(self):
        self.selection=(self.position,self.position)

    def add_markers(self,markers):
        self.markers=list(markers)
