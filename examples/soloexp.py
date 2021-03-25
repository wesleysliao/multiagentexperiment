
import cProfile

from asymsliderexperiment import \
    MessageTask, \
    ResetHandleTask, \
    SoloAsymForceTrackingTask

from humanfalconparticipant import HumanFalconParticipant

from multiagentexperiment import MultiAgentExperiment

import pyglet


class SoloSliderExperiment(MultiAgentExperiment):

    def __init__(self):
        super().__init__("SoloSlider")

        self.timestep = 1.0 / 60.0

        self.procedure.append([MessageTask("msgwelcome1",
                                           "Welcome to the Experiment 1",
                                           self.timestep, 3.0)])

        self.procedure.append([ResetHandleTask("0-reset1", self.timestep)])
        params = {"k":5.0, "push":1.0, "pull":1.0}
        self.procedure.append([SoloAsymForceTrackingTask("0-solo1",
                                                         self.timestep,
                                                         self.datafolder,
                                                         20.0,
                                                         parameters=params)])

        self.procedure.append([MessageTask("msgcomplete1",
                                           "Experiment Complete. 1",
                                           self.timestep, 4.0)])

        self.participants.append(HumanFalconParticipant("subject",
                                                        self.timestep, 0))

        pyglet.clock.schedule_interval(self.step, self.timestep)

    def completed(self):
        super().completed()
        pyglet.app.exit()


if __name__ == "__main__":

    experiment = SoloSliderExperiment()
    experiment.assign()

    cProfile.run("pyglet.app.run()", sort="tottime")
