#!/usr/bin/env python3

import copy
import csv
import datetime
import os

import numpy as np

from dynamicobject import DynamicObject, Damping, CompressionSpring, TensionSpring, BindPosition, PositionLimits



class Role:

    def __init__(self, handle_object, perspective=None):
        if perspective is None:
            self.perspective = Perspective()
        else:
            self.perspective = perspective
            
        self.participant = None
        self.handle_object = handle_object


    def assign(self, participant):
        self.participant = participant


    def get_positions(self, task_state):
        self.participant.get_action(self.perspective.task_to_view(task_state))
        self.handle_object.state[0] = self.perspective.handle_to_task(self.participant.handle.get_position())
            
    def update_forces(self):
        force = self.perspective.task_to_handle(self.handle_object.force)
        self.handle_object.force = 0.0
        self.participant.handle.update_force(force)



class Perspective:

    def task_to_handle(self, force):
        return force

        
    def handle_to_task(self, position):
        return position

        
    def task_to_view(self, task_state):
        perspective_state = task_state
        return perspective_state



class FlippedPerspective(Perspective):

    def task_to_handle(self, force):
        return -force
        
        
    def handle_to_task(self, position):
        return -position
        
        
    def task_to_view(self, task_state):
        perspective_state = copy.deepcopy(task_state)
        
        if "dynamic_objects" in perspective_state:
            for key, value in perspective_state["dynamic_objects"].items():
                state = value["state"]
                state[0] *= -1
                state[1] *= -1
                state[2] *= -1
                value["state"] = state
                
        if "reference_trajectories" in perspective_state:
            for key, value in perspective_state["reference_trajectories"].items():
                for point in range(len(value["full"])):
                    value["full"][point] *= -1
        return perspective_state



class Participant:

    def __init__(self, name, handle):
        self.name = name
        self.handle = handle


    def get_action(self, visible_state):

        self.agent.get_action(visible_state, handle_state)

        return self.handle.get_position()



class Handle():

    def __init__(self):
        self.x = 0.0
        self.force = 0.0
        
        
    def get_position(self):
        return self.x


    def update_force(self, force):
        self.force = force



class ReferenceTrajectory:

    def __init__(self, name,
                 trajectory_function = lambda x: np.zeros(np.array(x).shape),
                 tracking_axes = "y",
                 time_axes = "x",
                 time_window = [-1.0, 1.0],
                 timestep = 0.1):
        self.name = name
                
        self.trajectory_function = trajectory_function
        self.tracking_axes = tracking_axes
        self.time_axes = time_axes
        
        self.appearance = {}
        self.appearance["time_axes"] = self.time_axes
        
        self.time_window = time_window
        self.timestep = timestep
        
        self.now = 0
        self.update(self.now)
        
        
    def update(self, time):
        time_past = np.arange(time+self.time_window[0], time, self.timestep)
        self.past = self.trajectory_function(time_past)
        
        self.now = self.trajectory_function(time)
        
        time_future = np.linspace(time, time+self.time_window[1], int(self.time_window[1]/self.timestep), endpoint=True)
        self.future = self.trajectory_function(time_future)
                                                         
        self.full = []
        self.full.extend(self.past)
        self.full.extend([self.now])
        self.full.extend(self.future)
        
        self.timesteps = []
        self.timesteps.extend(time_past)
        self.timesteps.extend([time])
        self.timesteps.extend(time_future)



class MultiAgentTask:
    TASK_WAITING = 0
    TASK_RUNNING = 1
    TASK_COMPLETED = 2
    TASK_FAILED = 3
    
    def __init__(self, name, datafolder, timestep, duration=None):
    
        self.name = name

        self.roles = []
        self.dynamic_objects = []
        self.constraints = []
        self.reference_trajectories = []
        self.endconditions = []

        self.experimenttime = None
        
        self.datafolder = datafolder
        self.datafile = None

        self.timestep = timestep
        self.duration = duration
        self.reset()


    def add_obj(self, dynamicobject):
        self.dynamic_objects.append(dynamicobject)


    def add_constraint(self, constraint):
        self.constraints.append(constraint)


    def add_ref(self, reference_trajectory):
        self.reference_trajectories.append(reference_trajectory)
        
    
    def add_endcond(self, condition):
        self.endconditions.append(condition)
       

    def reset(self):
        self.time = 0.0
        self.taskstate = self.TASK_WAITING

        for dyn_obj in self.dynamic_objects:
            dyn_obj.reset()


    def start(self):
        time_now = datetime.datetime.now()
        datetime_str = time_now.strftime("%Y-%b%d-%H%M")
        
        self.filename = self.datafolder + "/" + self.name + "_" + datetime_str
        self.datafile = open(self.filename, 'w')
        
        fieldnames = self.get_header()
        self.datawriter = csv.DictWriter(self.datafile, fieldnames=fieldnames)
        self.datawriter.writeheader()
        
        
    def close(self):
        self.datafile.close()


    # The experiment is responsible for repeatedly calling step each timestep.
    # the task will assume that the time has elapsed.
    # This allows for faster than real-time execution for simulated participants.
    def step(self, experimenttime):
        self.time += self.timestep
        self.experimenttime = experimenttime
        
        
        if self.duration is not None and self.time >= self.duration:
            self.taskstate = self.TASK_COMPLETED
        else:
            self.taskstate = self.TASK_RUNNING
            
        for endcondition in self.endconditions:
            if endcondition.check():
                self.taskstate = self.TASK_COMPLETED
        
        state = self.get_state_dict()
        
        for ref_traj in self.reference_trajectories:
            ref_traj.update(self.time)
        
        for role in self.roles:
            role.get_positions(state)

        for constraint in self.constraints:
            constraint.apply()

        for role in self.roles:
            role.update_forces()
            
        for dyn_obj in self.dynamic_objects:
            dyn_obj.step(self.timestep)

            
        self.write_data(state)
        
        return self.taskstate
        
    
    def get_state_dict(self):
    
        state = {}
        state["task"] = self.name
        state["taskstate"] = self.taskstate
        state["tasktime"] = self.time
        state["experimenttime"] = self.experimenttime
        
        state["dynamic_objects"] = {}
        for dyn_obj in self.dynamic_objects:
            state["dynamic_objects"][dyn_obj.name] = {}
            state["dynamic_objects"][dyn_obj.name]["state"] = dyn_obj.state
            state["dynamic_objects"][dyn_obj.name]["appearance"] = dyn_obj.appearance
            
        state["reference_trajectories"] = {}
        for ref_traj in self.reference_trajectories:
            state["reference_trajectories"][ref_traj.name] = {}
            state["reference_trajectories"][ref_traj.name]["full"] = ref_traj.full
            state["reference_trajectories"][ref_traj.name]["timesteps"] = ref_traj.timesteps
            state["reference_trajectories"][ref_traj.name]["now"] = ref_traj.now
                                  
        return state
        
    def get_header(self):
        fieldnames = []
        
        fieldnames.append("task")
        fieldnames.append("taskstate")
        fieldnames.append("tasktime")
        fieldnames.append("experimenttime")
        fieldnames.append("task")
        
        for dyn_obj in self.dynamic_objects:
            fieldnames.append("object_"+dyn_obj.name+"_pos")
            fieldnames.append("object_"+dyn_obj.name+"_vel")
            fieldnames.append("object_"+dyn_obj.name+"_acc")
            
            
        
        for ref_traj in self.reference_trajectories:
            fieldnames.append("reference_"+ref_traj.name+"_now")
            
            
        return fieldnames
        
    def write_data(self, state_dict):
    
        data = {}
        data["task"] = state_dict["task"]
        data["taskstate"] = state_dict["taskstate"]
        data["tasktime"] = state_dict["tasktime"]
        data["experimenttime"] = state_dict["experimenttime"]
    
        for key, value in state_dict["dynamic_objects"].items():
            data["object_"+key+"_pos"] = value["state"][0]
            data["object_"+key+"_vel"] = value["state"][1]
            data["object_"+key+"_acc"] = value["state"][2]
        
        
        for key, value in state_dict["reference_trajectories"].items():
            data["reference_"+key+"_now"] = value["now"]
            
        
        self.datawriter.writerow(data)



class MultiAgentExperiment:

    def __init__(self,
                 datafolder_prefix):

        self.participants = []
        self.procedure = []
        self.datafolder_prefix = datafolder_prefix

        time_now = datetime.datetime.now()
        datetime_str = time_now.strftime("%Y-%b%d-%H%M")
        
        self.datafolder = "./data/" + self.datafolder_prefix + "_" + datetime_str
        
        os.mkdir(self.datafolder)
        print(self.datafolder)
        
        self.time = 0.0
        
        
    def assign(self):

        for trial in self.procedure:
            print(len(trial))
            participant_ndx = 0
            for task in trial:
                print(task.name, "roles:", len(task.roles), "participant:", end=" ")
                for role in task.roles:
                    print(participant_ndx, end=" ")
                    role.assign(self.participants[participant_ndx])
                    participant_ndx += 1
                print()
        self.active_trial = self.procedure[0]
        for task in self.active_trial:
            task.start()


    def step(self, dt):
    
        self.time += dt
    
        complete_tasks = 0
        for task in self.active_trial:
            taskstate = task.step(self.time)
        
            if taskstate == MultiAgentTask.TASK_COMPLETED:
               complete_tasks += 1
               
        if complete_tasks == len(self.active_trial): #all tasks done
            trialindex = self.procedure.index(self.active_trial)
            
            for task in self.active_trial:
                task.close()
            
            if (len(self.procedure) >  trialindex + 1):
                self.active_trial = self.procedure[trialindex + 1]
                    
                for task in self.active_trial:
                    task.start()
            else:
               self.completed()
        
    def completed(self):
        pass


            
            












