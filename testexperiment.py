
import numpy as np

import pyglet

from humanfalconparticipant import HumanFalconParticipant
from multiagentexperiment import Role, Participant, Perspective, FlippedPerspective, ReferenceTrajectory, MultiAgentTask, MultiAgentExperiment


from dynamicobject import DynamicObject, TensionSpring


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


class TestTask(MultiAgentTask):
   
    def __init__(self, name, duration, datafolder, timestep = 0.1):
        super().__init__(name, duration, datafolder, timestep=timestep)
        
        
        self.add_ref(ReferenceTrajectory("sos", trajectory_function = sos_gen()))
        
        p1_handle_obj = DynamicObject("p1_handle", 1.0, 
                                   initial_state=[-1.0, 0.0, 0.0],
                                   appearance={"shape":"circle", "radius":0.1, "color":(0, 0, 255)})
        self.add_obj(p1_handle_obj)
                                   
        p2_handle_obj = DynamicObject("p2_handle", 1.0, 
                                      initial_state=[1.0, 0.0, 0.0],
                                      appearance={"shape":"circle", "radius":0.1, "color":(255, 0, 255)})
        self.add_obj(p2_handle_obj)
        
        self.add_constraint(TensionSpring(p1_handle_obj, p2_handle_obj, 10.0, 0.1))
        self.add_constraint(TensionSpring(p2_handle_obj, p1_handle_obj, 10.0, 0.1))
                                   
        self.roles.append(Role(p1_handle_obj, perspective=Perspective()))
        self.roles.append(Role(p2_handle_obj, perspective=FlippedPerspective()))


class TestExperiment(MultiAgentExperiment):

    def __init__(self):
        super().__init__("TestExperiment")
        
        self.timestep = 1.0 / 120.0
        
        self.procedure.append(TestTask("test1", 20.0, self.datafolder, timestep=self.timestep))
        self.procedure.append(TestTask("test2", 20.0, self.datafolder, timestep=self.timestep))
        self.procedure.append(TestTask("test3", 20.0, self.datafolder, timestep=self.timestep))
        
        self.participants.append(HumanFalconParticipant("player1", self.timestep, 0))
        self.participants.append(HumanFalconParticipant("player2", self.timestep, 1))
       
        pyglet.clock.schedule_interval(self.step, self.timestep)
    
    def completed(self):
        super().completed()
        pyglet.app.exit()   
        

 
if __name__ == "__main__":

    experiment = TestExperiment()
    experiment.assign()
    
    pyglet.app.run()