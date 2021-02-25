


import cProfile
import copy


from dynamicobject import \
    BindPosition, \
    ConditionAND, \
    Damping, \
    DynamicObject, \
    InRangeForDuration, \
    PositionLimits, \
    PositionThreshold, \
    SpringLawSolid

from humanfalconparticipant import HumanFalconParticipant

from multiagentexperiment import \
    FlippedPerspective, \
    MultiAgentExperiment, \
    MultiAgentTask, \
    Perspective, \
    ReferenceTrajectory, \
    Role


import numpy as np

import pyglet


def sos_gen(zero_start=2.0, soft_start_s=5.0):

    frequencies = np.array([1.7, 1.3, 1.1, 0.7, 0.5])
    amplitudes = 1.0 / frequencies
    amplitudes /= np.sum(amplitudes)

    order = np.random.permutation(np.arange(len(frequencies)))
    a = amplitudes[order]
    f = frequencies[order]
    p = np.random.random(size=a.size) * 2.0 * np.pi

    def sos_fn(t):
        result = 0
        for i in range(len(amplitudes)):
            result += (a[i] * np.sin(f[i] * np.pi * (t + p[i])))

        result *= (t > zero_start)
        result *= 1.0 - (np.maximum(soft_start_s + zero_start - t, 0.0)
                         / soft_start_s)
        return result

    return sos_fn


def flat_gen():
    def flat_fn(t):
        return t * 0.0
    return flat_fn


class HiddenObjectsPerspective(Perspective):

    def __init__(self, hidden_obj_names):
        self.hidden_obj_names = hidden_obj_names

    def task_to_view(self, task_state):
        perspective_state = copy.deepcopy(task_state)
        if 'dynamic_objects' in task_state:
            for key, value in task_state['dynamic_objects'].items():
                if key in self.hidden_obj_names:
                    perspective_state['dynamic_objects'].pop(key)
                    
        return perspective_state


class FlippedHiddenObjectsPerspective(FlippedPerspective):

    def __init__(self, hidden_obj_names):
        self.hidden_obj_names = hidden_obj_names

    def task_to_view(self, task_state):
        perspective_state = copy.deepcopy(task_state)
        if 'dynamic_objects' in task_state:
            for key, value in task_state['dynamic_objects'].items():
                if key in self.hidden_obj_names:
                    perspective_state['dynamic_objects'].pop(key)

        return super().task_to_view(perspective_state)


class BlankTask(MultiAgentTask):

    def __init__(self, name, timestep, datafolder=None, duration=None):
        super().__init__(name,
                         timestep,
                         datafolder=datafolder,
                         duration=duration)

        handle_obj = DynamicObject('handle', 0.0)
        self.add_obj(handle_obj)
        self.roles.append(Role(handle_obj))


class MessageTask(MultiAgentTask):

    def __init__(self, name, message, timestep, duration):
        super().__init__(name, timestep, duration=duration)

        self.message = message

        handle_obj = DynamicObject('handle', 0.0)
        self.add_obj(handle_obj)
        self.roles.append(Role(handle_obj))

    def get_state_dict(self):
        state = super().get_state_dict()
        state['task_message'] = self.message
        return state


class ResetHandleTask(MessageTask):

    def __init__(self, name, timestep):
        super().__init__(name,
                         'Gently pull your handle toward you until the handle stops.',
                         timestep, None)

        handle_obj = self.dynamic_objects[0]
        self.add_endcond(PositionThreshold(handle_obj, -0.8, check_greater=False))



class CenterHandleTask(MultiAgentTask):

    def __init__(self, name,  timestep, duration):
        super().__init__(name,
                         timestep,
                         duration=duration)

        self.message = 'Align your cursor (blue) with the line. When both subjects are aligned, the task will start.'

        self.add_ref(ReferenceTrajectory('flat',
                                         trajectory_function=flat_gen()))

        obj_radius = 0.05

        self_color = (0, 0, 255)
        other_color = (255, 0, 127)

        p1_handle_obj = DynamicObject('p1_handle', 0.0,
                                      initial_state=[-1.0, 0.0, 0.0],
                                      record_data=False,
                                      appearance={'shape': 'circle',
                                                  'radius': obj_radius,
                                                  'color': self_color})

        p1_handle_draw = DynamicObject('p1_handle_draw', 0.0,
                                       initial_state=[-1.0, 0.0, 0.0],
                                       record_data=False,
                                       appearance={'shape': 'circle',
                                                   'radius': obj_radius,
                                                   'color': other_color})

        p2_handle_obj = DynamicObject('p2_handle', 0.0,
                                      initial_state=[1.0, 0.0, 0.0],
                                      record_data=False,
                                      appearance={'shape': 'circle',
                                                  'radius': obj_radius,
                                                  'color': self_color})

        p2_handle_draw = DynamicObject('p2_handle_draw', 0.0,
                                       initial_state=[1.0, 0.0, 0.0],
                                       record_data=False,
                                       appearance={'shape': 'circle',
                                                   'radius': obj_radius,
                                                   'color': other_color})

        self.add_obj(p1_handle_draw)
        self.add_obj(p2_handle_draw)

        self.add_obj(p1_handle_obj)
        self.add_obj(p2_handle_obj)


        self.add_constraint(BindPosition(p1_handle_draw, p1_handle_obj))
        self.add_constraint(BindPosition(p2_handle_draw, p2_handle_obj))

        self.roles.append(Role(p1_handle_obj,
                               perspective=HiddenObjectsPerspective(
                                   ['p1_handle_draw',
                                    'p2_handle'])))
        self.roles.append(Role(p2_handle_obj,
                               perspective=FlippedHiddenObjectsPerspective(
                                   ['p2_handle_draw',
                                    'p1_handle'])))

        self.add_endcond(ConditionAND([
            InRangeForDuration(p1_handle_obj, 0.2, -0.2, duration_s=1.0),
            InRangeForDuration(p2_handle_obj, 0.2, -0.2, duration_s=1.0),
        ]))

    def get_state_dict(self):
        state = super().get_state_dict()
        state['task_message'] = self.message
        return state



class SoloAsymForceTrackingTask(MultiAgentTask):

    def __init__(self, name, timestep, datafolder, duration, parameters):
        super().__init__(name,
                         timestep,
                         datafolder=datafolder,
                         duration=duration,
                         parameters=parameters)

        k = parameters.get('k', 10.0)
        push = parameters.get('push', 1.0)
        pull = parameters.get('pull', 1.0)

        self.add_ref(ReferenceTrajectory('sos',
                                         trajectory_function=sos_gen()))

        obj_radius = 0.05
        rest_length = obj_radius * 8

        cursor_color = (220, 220, 220)
        self_color = (0,0,255)
        link_color = (0, 64, 128)

        handle_obj = DynamicObject('handle', 0.0,
                                   initial_state=[-1.0, 0.0, 0.0],
                                         appearance={'shape': 'circle',
                                                     'radius': obj_radius/2.0,
                                                     'color': link_color})

        handle_draw = DynamicObject('handle_draw', 0.0,
                                    initial_state=[-1.0, 0.0, 0.0],
                                    record_data=False,
                                    appearance={'shape': 'circle',
                                                'radius': obj_radius,
                                                'color': self_color})

        cursor = DynamicObject('cursor', 0.1,
                               initial_state=[0.0, 0.0, 0.0],
                               appearance={'shape': 'rectangle',
                                           'width': obj_radius * 3.0,
                                           'height': obj_radius * 1.75,
                                           'color': cursor_color})

        self_contact_obj = DynamicObject('self_contact', 0.0,
                                         initial_state=[0.0, 0.0, 0.0],
                                         record_data=False,
                                         appearance={'shape': 'circle',
                                                     'radius': obj_radius/2.0,
                                                     'color': self_color})

        self_contact_link = DynamicObject('self_contact_link', 0.0,
                                          initial_state=[0.0, 0.0, 0.0],
                                          record_data=False,
                                          appearance={'shape': 'link',
                                                      'linktype': 'bulge',
                                                      'start_ref': 'p1_self_contact',
                                                      'start_ref': 'self_contact',
                                                      'end_ref': 'handle_draw',
                                                      'color': link_color})
        self.add_obj(handle_obj)
        self.add_obj(cursor)

        self.add_obj(self_contact_link)
        self.add_obj(self_contact_obj)
        self.add_obj(handle_draw)

        self.add_pre_constraint(BindPosition(self_contact_obj,
                                             cursor,
                                             offset=-obj_radius))

        self.add_constraint(BindPosition(handle_draw, handle_obj))
        self.add_constraint(PositionLimits(handle_draw,
                                           pos=-(rest_length/2),
                                           reference=cursor))

        self.add_constraint(SpringLawSolid(handle_obj, cursor,
                                           -k, -rest_length))
        self.add_constraint(SpringLawSolid(cursor, handle_obj,
                                           k*push, -rest_length))

        self.add_constraint(SpringLawSolid(handle_obj, cursor,
                                           k, rest_length))
        self.add_constraint(SpringLawSolid(cursor, handle_obj,
                                           -k*pull, rest_length))

        self.add_constraint(Damping(1, cursor))

        self.roles.append(Role(handle_obj))


class DyadAsymForceTrackingTask(MultiAgentTask):

    def __init__(self, name,  timestep, datafolder, duration, parameters):
        super().__init__(name,
                         timestep,
                         datafolder=datafolder,
                         duration=duration,
                         parameters=parameters)

        k = parameters.get('k', 10.0)
        p1_push = parameters.get('p1_push', 1.0)
        p1_pull = parameters.get('p1_pull', 1.0)
        p2_push = parameters.get('p2_push', 1.0)
        p2_pull = parameters.get('p2_pull', 1.0)

        self.add_ref(ReferenceTrajectory('sos', trajectory_function = sos_gen()))

        obj_radius = 0.05
        rest_length = obj_radius * 4

        cursor_color = (220, 220, 220)
        self_color = (0,0,255)
        link_color = (0, 64, 128)
        other_color = (255, 0, 255)

        p1_handle_obj = DynamicObject('p1_handle', 0.0,
                                      initial_state=[-0.0, 0.0, 0.0])
        p1_handle_draw = DynamicObject('p1_handle_draw', 0.0,
                                       initial_state=[-0.0, 0.0, 0.0],
                                       record_data=False,
                                       appearance={'shape': 'circle',
                                                   'radius': obj_radius,
                                                   'color': self_color})

        p2_handle_obj = DynamicObject('p2_handle', 0.0,
                                      initial_state=[0.0, 0.0, 0.0])

        p2_handle_draw = DynamicObject('p2_handle_draw', 0.0,
                                       initial_state=[0.0, 0.0, 0.0],
                                       record_data=False,
                                       appearance={'shape': 'circle',
                                                   'radius': obj_radius,
                                                   'color':self_color})

        cursor = DynamicObject('cursor', 0.1,
                               initial_state=[0.0, 0.0, 0.0],
                               appearance={'shape':'rectangle',
                                           'width':obj_radius * 3.0,
                                           'height':obj_radius * 1.0,
                                           'color':cursor_color})

        p1_self_contact_obj = DynamicObject('p1_self_contact', 0.0,
                                            initial_state=[0.0, 0.0, 0.0],
                                            record_data=False,
                                            appearance={'shape':'circle',
                                                        'radius':obj_radius/2,
                                                        'color':self_color})

        p1_contact_link = DynamicObject('p1_contact_link', 0.0,
                                        initial_state=[0.0, 0.0, 0.0],
                                        record_data=False,
                                        appearance={'shape': 'link',
                                                    'linktype': 'bulge',
                                                    'start_ref': 'p1_self_contact',
                                                    'end_ref': 'p1_handle_draw',
                                                    'color': link_color})

        p1_other_contact_obj = DynamicObject('p1_other_contact', 0.0,
                                             initial_state=[0.0, 0.0, 0.0],
                                             record_data=False,
                                             appearance={'shape':'circle',
                                                         'radius':obj_radius/2,
                                                         'color':other_color})

        p2_self_contact_obj = DynamicObject('p2_self_contact', 0.0,
                                            initial_state=[0.0, 0.0, 0.0],
                                            record_data=False,
                                            appearance={'shape':'circle',
                                                        'radius':obj_radius/2,
                                                        'color':self_color})

        p2_contact_link = DynamicObject('p2_contact_link', 0.0,
                                        initial_state=[0.0, 0.0, 0.0],
                                        record_data=False,
                                        appearance={'shape': 'link',
                                                    'linktype': 'bulge',
                                                    'start_ref': 'p1_self_contact',
                                                    'start_ref': 'p2_self_contact',
                                                    'end_ref': 'p2_handle_draw',
                                                    'color': link_color})

        p2_other_contact_obj = DynamicObject('p2_other_contact', 0.0,
                                             initial_state=[0.0, 0.0, 0.0],
                                             record_data=False,
                                             appearance={'shape':'circle',
                                                         'radius':obj_radius/2,
                                                         'color':other_color})

        self.add_obj(p1_handle_obj)
        self.add_obj(p2_handle_obj)
        self.add_obj(cursor)

        self.add_obj(p1_contact_link)
        self.add_obj(p1_self_contact_obj)
        self.add_obj(p1_other_contact_obj)
        self.add_obj(p2_contact_link)
        self.add_obj(p2_self_contact_obj)
        self.add_obj(p2_other_contact_obj)

        self.add_obj(p1_handle_draw)
        self.add_obj(p2_handle_draw)

        self.add_pre_constraint(BindPosition(p1_self_contact_obj, cursor,
                                             offset=-obj_radius))
        self.add_pre_constraint(BindPosition(p1_other_contact_obj, cursor,
                                             offset=obj_radius))
        self.add_pre_constraint(BindPosition(p2_self_contact_obj, cursor,
                                             offset=obj_radius))
        self.add_pre_constraint(BindPosition(p2_other_contact_obj, cursor,
                                             offset=-obj_radius))

        self.add_constraint(BindPosition(p1_handle_draw, p1_handle_obj))
        self.add_constraint(PositionLimits(p1_handle_draw,
                                           pos=-rest_length,
                                           reference=cursor))
        self.add_constraint(BindPosition(p2_handle_draw, p2_handle_obj))
        self.add_constraint(PositionLimits(p2_handle_draw,
                                           neg=rest_length,
                                           reference=cursor))

        self.add_constraint(SpringLawSolid(p1_handle_obj, cursor,
                                           -k, -rest_length))
        self.add_constraint(SpringLawSolid(cursor, p1_handle_obj,
                                           k*p1_push, rest_length))
        self.add_constraint(SpringLawSolid(p1_handle_obj, cursor,
                                           k, rest_length))
        self.add_constraint(SpringLawSolid(cursor, p1_handle_obj,
                                           -k*p1_pull, -rest_length))

        self.add_constraint(SpringLawSolid(p2_handle_obj, cursor,
                                           k, rest_length))
        self.add_constraint(SpringLawSolid(cursor, p2_handle_obj,
                                           -k*p2_push, -rest_length))
        self.add_constraint(SpringLawSolid(p2_handle_obj, cursor,
                                           -k, -rest_length))
        self.add_constraint(SpringLawSolid(cursor, p2_handle_obj,
                                           k*p2_pull, rest_length))

        self.add_constraint(Damping(1, cursor))

        self.roles.append(Role(p1_handle_obj,
                               perspective=HiddenObjectsPerspective(['p2_handle_draw',
                                                                     'p2_self_contact',
                                                                     'p2_contact_link',
                                                                     'p2_other_contact'])))
        self.roles.append(Role(p2_handle_obj,
                               perspective=FlippedHiddenObjectsPerspective(['p1_handle_draw',
                                                                            'p1_self_contact',
                                                                            'p1_contact_link',
                                                                            'p1_other_contact'])))


class AsymmetricDyadSliderExperiment(MultiAgentExperiment):

    def __init__(self):
        super().__init__('AsymDyadSlider')

        self.timestep = 1.0 / 70.0

        duration = 60.0
        k = 5.0

        self.procedure.append([MessageTask('msgwelcome1',
                                           'Welcome to the Experiment 1',
                                           self.timestep, 3.0),
                               MessageTask('msgwelcome2',
                                           'Welcome to the Experiment 2',
                                           self.timestep, 3.0)])

        self.procedure.append([CenterHandleTask('1-reset',
                                                self.timestep,
                                                duration=None)])

        params1 = {'k': k,
                   'p1_push': 1.0, 'p1_pull': 1.0,
                   'p2_push': 1.0, 'p2_pull': 1.0}
        self.procedure.append([DyadAsymForceTrackingTask('1-dyad',
                                                         self.timestep,
                                                         self.datafolder,
                                                         duration,
                                                         parameters=params1)])
        
        self.procedure.append([CenterHandleTask('2-reset',
                                                self.timestep,
                                                duration=None)])

        params2 = {'k': k,
                   'p1_push': 0.5, 'p1_pull': 1.0,
                   'p2_push': 0.5, 'p2_pull': 1.0}
        self.procedure.append([DyadAsymForceTrackingTask('2-dyad',
                                                         self.timestep,
                                                         self.datafolder,
                                                         duration,
                                                         parameters=params2)])

        self.procedure.append([CenterHandleTask('3-reset',
                                                self.timestep,
                                                duration=None)])
        params3 = {'k': k,
                   'p1_push': 1.0, 'p1_pull': 0.5,
                   'p2_push': 1.0, 'p2_pull': 0.5}
        self.procedure.append([DyadAsymForceTrackingTask('3-dyad',
                                                         self.timestep,
                                                         self.datafolder,
                                                         duration,
                                                         parameters=params3)])

        self.procedure.append([MessageTask('msgcomplete1',
                                           'Experiment Complete. 1',
                                           self.timestep,
                                           5.0),
                               MessageTask('msgcomplete2',
                                           'Experiment Complete. 2',
                                           self.timestep,
                                           5.0)])

        self.participants.append(HumanFalconParticipant('player1',
                                                        self.timestep,
                                                        0))
        self.participants.append(HumanFalconParticipant('player2',
                                                        self.timestep,
                                                        1))

        pyglet.clock.schedule_interval(self.step, self.timestep)

    def completed(self):
        super().completed()
        pyglet.app.exit()


if __name__ == '__main__':

    experiment = AsymmetricDyadSliderExperiment()
    experiment.assign()

    cProfile.run('pyglet.app.run()', sort='tottime')
