#!/usr/bin/env python3

import time
import threading
from queue import Queue

import pyglet

from multiagentexperiment import Participant, Handle
from falcon_c.falcon import NovintFalcon



class FalconHapticHandle(Handle):

    def __init__(self, falcon_device_num):

        self.timestep_s = 1.0 / 1000
        self.falcon = NovintFalcon(self.timestep_s, falcon_device_num)
        if falcon_device_num==0:
            self.falcon.set_leds(0, 1, 0)
        elif falcon_device_num==1:
            self.falcon.set_leds(0, 0, 1)
            
        
        super().__init__()

        self.shutdown_flag = threading.Event()
        self.shutdown_flag.clear()
        falcon_io_loop = threading.Thread(target=self.update_falcon)
        falcon_io_loop.start()

    
    def get_position(self):
        pos = self.falcon.get_pos()
        return -pos[2]

    def get_velocity(self):
        vel = self.falcon.get_vel()
        return -vel[2]

    def update_falcon(self):
        start_time = time.monotonic()
        io_loop_count = 0
        while not self.shutdown_flag.is_set():

            while True:
                elapsed_time = time.monotonic() - start_time
                expected_loops = int(elapsed_time / self.timestep_s)
                if io_loop_count > expected_loops:
                    sleep_time = (io_loop_count * self.timestep_s) - elapsed_time
                    time.sleep(sleep_time)
                else:
                    break

            self.falcon.update_state()

            self.falcon.add_force(0, 0, self.force)
            self.falcon.output_forces()

            io_loop_count += 1


    def update_force(self, force):
        super().update_force(-force)


    def shutdown(self):
        self.shutdown_flag.set()
        super().shutdown()
    

class HumanFalconParticipant(Participant):
    
    def __init__(self, name, timestep_s, falcon_device_num):
        
        display = pyglet.canvas.get_display()
        screen = display.get_screens()[falcon_device_num]
        self.window = pyglet.window.Window(screen.width, screen.height, 
                                           screen=screen,
                                           style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
        self.window.set_location(screen.x, screen.y)
        
        window_size = self.window.get_size()
        self.scale = window_size[0] / 2;
        self.offset = (0, (window_size[1] / 2) - self.scale)
    
        self.visible_state = {}
        self.window.on_draw = self.on_draw
        self.fps_display = pyglet.window.FPSDisplay(window=self.window)
        
        
        super().__init__(name, FalconHapticHandle(falcon_device_num))
        
       
    
    def on_draw(self):
    
        self.window.clear()
                
        if "reference_trajectories" in self.visible_state:
            for key, value in self.visible_state["reference_trajectories"].items():
                for point_ndx, point in enumerate(value["full"]):
                    if point_ndx == 0:
                        continue
                    last_point = value["full"][point_ndx - 1]
                    x1 = self.offset[0] + self.scale + ((value["timesteps"][point_ndx - 1] - self.visible_state["tasktime"]) * self.scale)
                    y1 = self.offset[1] + self.scale + (last_point * self.scale)
                    x2 = self.offset[0] + self.scale + ((value["timesteps"][point_ndx] - self.visible_state["tasktime"]) * self.scale)
                    y2 = self.offset[1] + self.scale + (point * self.scale)
                    pyglet.shapes.Line(x1, y1, x2, y2, 
                                       width=10, 
                                       color=(200,200,200)).draw()
        

        if "dynamic_objects" in self.visible_state:
            for key, value in self.visible_state["dynamic_objects"].items():
                if value["appearance"] is None:
                    continue
                if value["appearance"]["shape"] == "circle":
                    x = self.offset[0] + self.scale
                    y = self.offset[1] + self.scale + (value["state"][0] * self.scale)
                    radius = self.scale * value["appearance"]["radius"]
                    color = value["appearance"]["color"]
                    pyglet.shapes.Circle(x, y, radius, color=color).draw()
                
                elif value["appearance"]["shape"] == "rectangle":
                
                    width = self.scale * value["appearance"]["width"]
                    height = self.scale * value["appearance"]["height"]
                    x = self.offset[0] + self.scale - (width / 2.0)
                    y = self.offset[1] + self.scale  - (height / 2.0) + (value["state"][0] * self.scale)
                    color = value["appearance"]["color"]
                    border = 0.0
                    if "border" in value["appearance"]:
                        border = self.scale * value["appearance"]["border"]
                    border_color = color
                    if "border_color" in value["appearance"]:
                        border_color = value["appearance"]["border_color"]
                    pyglet.shapes.BorderedRectangle(x, y, width, height, border=border, color=color, border_color=border_color).draw()
                  
        if "task_message" in self.visible_state:
            pyglet.text.Label(self.visible_state["task_message"],
                              font_name="FreeMono", font_size=12,
                              x= self.offset[0] + self.scale, 
                              y= self.offset[1] + self.scale,
                              anchor_x="center", anchor_y="center").draw()

        self.fps_display.draw()
 
    
    def get_action(self, visible_state): 
        self.visible_state = visible_state



    
        
