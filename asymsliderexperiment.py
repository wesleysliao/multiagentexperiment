
import copy


import numpy as np

import pyglet

from dynamicobject import DynamicObject, SpringLawSolid, BindPosition, PositionLimits
from humanfalconparticipant import HumanFalconParticipant
from multiagentexperiment import Role, Participant, Perspective, FlippedPerspective, ReferenceTrajectory, MultiAgentTask, MultiAgentExperiment


def sos_gen():
    amplitudes = [0.4, 0.3, 0.2, 0.1]
    frequencies = [0.4, 0.3, 0.2, 0.1]
    
    a = np.random.permutation(amplitudes)
    f = np.random.permutation(frequencies)
    p = np.random.random(size=a.size) * 2.0 * np.pi
    
    def sos_fn(t):
        result = 0
        for i in range(len(amplitudes)):
            result += (a[i] * np.sin(f[i] * np.pi * (t + p[i])))
        return result
        
    return sos_fn


class HiddenObjectsPerspective(Perspective):
    def __init__(self, hidden_obj_names):
        self.hidden_obj_names = hidden_obj_names
        
    def task_to_view(self, task_state):
        perspective_state = copy.deepcopy(task_state)
        if "dynamic_objects" in task_state:
            for key, value in task_state["dynamic_objects"].items():
                if key in self.hidden_obj_names:
                    perspective_state["dynamic_objects"].pop(key)
                    
        return perspective_state
         


class FlippedHiddenObjectsPerspective(FlippedPerspective):
    def __init__(self, hidden_obj_names):
        self.hidden_obj_names = hidden_obj_names
        
    def task_to_view(self, task_state):
        perspective_state = copy.deepcopy(task_state)
        if "dynamic_objects" in task_state:
            for key, value in task_state["dynamic_objects"].items():
                if key in self.hidden_obj_names:
                    perspective_state["dynamic_objects"].pop(key)
                    
        return super().task_to_view(perspective_state)
         


class MessageTask(MultiAgentTask):
  
    def __init__(self, name, message, duration, datafolder, timestep):
        super().__init__(name, duration, datafolder, timestep)
        
        self.message = message
  
        p1_handle_obj = DynamicObject("p1_handle", 0.0)
        p2_handle_obj = DynamicObject("p2_handle", 0.0)
        self.add_obj(p1_handle_obj)
        self.add_obj(p2_handle_obj)
        self.roles.append(Role(p1_handle_obj))
        self.roles.append(Role(p2_handle_obj))
        
    def get_state_dict(self):
        state = super().get_state_dict()
        state["task_message"] = self.message        
        return state



class AsymForceTrackingTask(MultiAgentTask):
   
    def __init__(self, name, duration, datafolder, timestep):
        super().__init__(name, duration, datafolder, timestep)
        
        
        self.add_ref(ReferenceTrajectory("sos", trajectory_function = sos_gen()))
        
        obj_radius = 0.05
        
        cursor_color = (220, 220, 220)
        self_color = (0,0,255)
        other_color = (255, 0, 255)
        
        p1_handle_obj = DynamicObject("p1_handle", 0.0, 
                                      initial_state=[-1.0, 0.0, 0.0])
        p1_handle_draw = DynamicObject("p1_handle_draw", 0.0, 
                                       initial_state=[-1.0, 0.0, 0.0],
                                       appearance={"shape":"circle",
                                                   "radius":obj_radius,
                                                   "color":self_color})
                                   
        p2_handle_obj = DynamicObject("p2_handle", 0.0, 
                                      initial_state=[1.0, 0.0, 0.0])
                                      
        p2_handle_draw = DynamicObject("p2_handle_draw", 0.0, 
                                       initial_state=[1.0, 0.0, 0.0],
                                       appearance={"shape":"circle",
                                                   "radius":obj_radius, 
                                                   "color":self_color})
        
        cursor = DynamicObject("cursor", 0.1, 
                               initial_state=[0.0, 0.0, 0.0],
                               appearance={"shape":"circle", 
                                           "radius":obj_radius, 
                                           "color":cursor_color})
        
        p1_self_contact_obj = DynamicObject("p1_self_contact", 0.0, 
                                            initial_state=[0.0, 0.0, 0.0],
                                            appearance={"shape":"circle", 
                                                        "radius":obj_radius/2, 
                                                        "color":self_color})
                                               
        p1_other_contact_obj = DynamicObject("p1_other_contact", 0.0, 
                                             initial_state=[0.0, 0.0, 0.0],
                                             appearance={"shape":"circle", 
                                                         "radius":obj_radius/2, 
                                                         "color":other_color})
       
        p2_self_contact_obj = DynamicObject("p2_self_contact", 0.0, 
                                            initial_state=[0.0, 0.0, 0.0],
                                            appearance={"shape":"circle", 
                                                        "radius":obj_radius/2, 
                                                        "color":self_color})
                                               
        p2_other_contact_obj = DynamicObject("p2_other_contact", 0.0, 
                                             initial_state=[0.0, 0.0, 0.0],
                                             appearance={"shape":"circle", 
                                                         "radius":obj_radius/2, 
                                                         "color":other_color})
        
        self.add_obj(p1_handle_obj)
        self.add_obj(p2_handle_obj)
        self.add_obj(cursor)
        
        self.add_obj(p1_self_contact_obj)
        self.add_obj(p1_other_contact_obj)
        self.add_obj(p2_self_contact_obj)
        self.add_obj(p2_other_contact_obj)
        
        self.add_obj(p1_handle_draw)
        self.add_obj(p2_handle_draw)
        
        self.add_constraint(BindPosition(p1_self_contact_obj, cursor, offset=-obj_radius))
        self.add_constraint(BindPosition(p1_other_contact_obj, cursor, offset=obj_radius)) 
        self.add_constraint(BindPosition(p2_self_contact_obj, cursor, offset=obj_radius))
        self.add_constraint(BindPosition(p2_other_contact_obj, cursor, offset=-obj_radius))
        
        self.add_constraint(BindPosition(p1_handle_draw, p1_handle_obj))
        self.add_constraint(PositionLimits(p1_handle_draw, pos=-(2 * obj_radius), reference=cursor))
        self.add_constraint(BindPosition(p2_handle_draw, p2_handle_obj))
        self.add_constraint(PositionLimits(p2_handle_draw, neg=(2 * obj_radius), reference=cursor))
        
        self.add_constraint(SpringLawSolid(p1_handle_obj, cursor, -10.0, -(obj_radius * 2)))
        self.add_constraint(SpringLawSolid(cursor, p1_handle_obj, 10.0, (obj_radius * 2)))
        self.add_constraint(SpringLawSolid(p2_handle_obj, cursor, 10.0, (obj_radius*2)))
        self.add_constraint(SpringLawSolid(cursor, p2_handle_obj, -10.0, -(obj_radius * 2)))
        
        self.roles.append(Role(p1_handle_obj, 
                               perspective=HiddenObjectsPerspective(["p2_handle_draw",
                                                                     "p2_self_contact",
                                                                     "p2_other_contact"])))
        self.roles.append(Role(p2_handle_obj, 
                               perspective=FlippedHiddenObjectsPerspective(["p1_handle_draw",
                                                                            "p1_self_contact",
                                                                            "p1_other_contact"])))


class AsymmetricDyadSliderExperiment(MultiAgentExperiment):

    def __init__(self):
        super().__init__("AsymDyadSlider")
        
        self.timestep = 1.0 / 120.0
        
        self.procedure.append(MessageTask("msgwelcome", "Welcome to the Experiment", 10.0, self.datafolder, self.timestep))
        self.procedure.append(AsymForceTrackingTask("0-equal", 10.0, self.datafolder, self.timestep))
        self.procedure.append(AsymForceTrackingTask("1-equal", 10.0, self.datafolder, self.timestep))
        self.procedure.append(AsymForceTrackingTask("2-equal", 10.0, self.datafolder, self.timestep))
        self.procedure.append(MessageTask("msgcomplete", "Experiment Complete.", 10.0, self.datafolder, self.timestep))
        
        self.participants.append(HumanFalconParticipant("player1", self.timestep, 0))
        self.participants.append(HumanFalconParticipant("player2", self.timestep, 1))
       
        pyglet.clock.schedule_interval(self.step, self.timestep)
    
    def completed(self):
        super().completed()
        pyglet.app.exit()   
        

 
if __name__ == "__main__":

    experiment = AsymmetricDyadSliderExperiment()
    experiment.assign()
    
    pyglet.app.run()