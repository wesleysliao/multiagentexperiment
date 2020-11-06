#!/usr/bin/env python3

from queue import Queue

import pyglet

from multiagentexperiment import Participant, Handle
from falcon_c.falcon import NovintFalcon



class FalconHapticHandle(Handle):

    def __init__(self, timestep_s, falcon_device_num):
    
        self.falcon = NovintFalcon(timestep_s, falcon_device_num)
        
        pyglet.clock.schedule_interval(self.falcon.update_state, 0.001)
        
        super().__init__()
    
    def get_position(self):
        pos = self.falcon.get_pos()
        
        return -pos[2]
        
    def update_force(self, force):
        self.falcon.add_force(0, 0, -force)
        self.falcon.output_forces()
        super().update_force(-force)
    

class HumanFalconParticipant(Participant):
    
    def __init__(self, name, timestep_s, falcon_device_num):
        
        self.scale = 320
        self.window = pyglet.window.Window(2 * self.scale, 2 * self.scale)
    
        self.visible_state = {}
        self.window.on_draw = self.on_draw
        self.fps_display = pyglet.window.FPSDisplay(window=self.window)
        
        
        super().__init__(name, FalconHapticHandle(timestep_s, falcon_device_num))
    
    
    def on_draw(self):
    
        self.window.clear()
        batch = pyglet.graphics.Batch()
        
        lines = []
        if "reference_trajectories" in self.visible_state:
            for key, value in self.visible_state["reference_trajectories"].items():
                for point_ndx, point in enumerate(value["full"]):
                    if point_ndx == 0:
                        continue
                    last_point = value["full"][point_ndx - 1]
                    x1 = self.scale + ((value["timesteps"][point_ndx - 1] - self.visible_state["tasktime"]) * self.scale)
                    y1 = self.scale + (last_point * self.scale)
                    x2 = self.scale + ((value["timesteps"][point_ndx] - self.visible_state["tasktime"]) * self.scale)
                    y2 = self.scale + (point * self.scale)
                    lines.append(pyglet.shapes.Line(x1, y1, x2, y2, 
                                       width=10, 
                                       color=(200,200,200),
                                       batch=batch))
                    
        objs = []
        if "dynamic_objects" in self.visible_state:
            for key, value in self.visible_state["dynamic_objects"].items():
                if value["appearance"] is None:
                    continue
                if value["appearance"]["shape"] == "circle":
                    x = self.scale
                    y = self.scale + (value["state"][0] * self.scale)
                    radius = self.scale * value["appearance"]["radius"]
                    color = value["appearance"]["color"]
                    objs.append(pyglet.shapes.Circle(x, y, radius, color=color, batch=batch))
        
        batch.draw()
        self.fps_display.draw()
        
        if "task_message" in self.visible_state:
            label=pyglet.text.Label(self.visible_state["task_message"],
                                    font_name="FreeMono", font_size=12,
                                    x=self.scale, y=self.scale,
                                    anchor_x="center", anchor_y="center")
            label.draw()
        
    
    def get_action(self, visible_state): 
        self.visible_state = visible_state



    
        
