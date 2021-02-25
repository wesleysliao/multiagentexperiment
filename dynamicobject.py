#!/usr/bin/env python3


import numpy as np


class DynamicObject:
    POS = 0
    VEL = 1
    ACC = 2

    def __init__(self,
                 name,
                 mass,
                 initial_state=[0.0, 0.0, 0.0],
                 record_data=True,
                 appearance=None):

        self.name = name
        self.appearance = appearance
        self.record_data = record_data

        self.mass = mass
        self.state = np.zeros((3,))
        self.queued_force = 0.0
        self.force = 0.0

        self.initial_state = initial_state
        self.reset()

    def reset(self):

        self.state = self.initial_state

    def step(self, dt_s):
        self.force = self.queued_force
        if self.mass > 0.0:
            self.state[self.ACC] = (self.force / self.mass)
        self.queued_force = 0.0
        self.state[self.VEL] += self.state[self.ACC] * dt_s
        self.state[self.POS] += self.state[self.VEL] * dt_s

    def add_force(self, force):
        self.queued_force += force


class Constraint:

    def __init__(self, target):
        self.target = target
        self.references = []

    def apply(self):
        pass



class Damping(Constraint):

    def __init__(self, b, target):
        self.b = b
        super().__init__(target)

    def apply(self):
        force = (self.target.state[1] * -self.b)
        self.target.add_force(force)


class CompressionSpring(Constraint):

    def __init__(self, target, reference, spring_coeff, resting_length):
        self.spring_coeff = spring_coeff
        self.resting_length = resting_length
        super().__init__(target)
        self.references.append(reference)

    def apply(self):

        pos1 = self.target.state[0]
        pos2 = self.references[0].state[0]

        compression = (pos2 + self.resting_length) - pos1
        if compression > 0:
            force = compression * self.spring_coeff

            self.target.add_force(force)


class TensionSpring(Constraint):

    def __init__(self, target, reference, spring_coeff, resting_length):
        self.spring_coeff = spring_coeff
        self.resting_length = resting_length
        super().__init__(target)
        self.references.append(reference)

    def apply(self):

        pos1 = self.target.state[0]
        pos2 = self.references[0].state[0]

        tension = pos1 - (pos2 + self.resting_length)
        if tension > 0:
            force = tension * -self.spring_coeff

            self.target.add_force(force)


class BindPosition(Constraint):

    def __init__(self, target, reference, offset=0.0, proportion=1.0):
        super().__init__(target)
        self.references.append(reference)
        self.offset = offset
        self.proportion = proportion

    def apply(self):
        self.target.state[0] = ((self.references[0].state[0]
                                 * self.proportion)
                                + self.offset)


class PositionLimits(Constraint):

    def __init__(self, target, pos=None, neg=None, reference=None):
        self.bound_pos = pos
        self.bound_neg = neg

        super().__init__(target)
        if reference is not None:
            self.references.append(reference)

    def apply(self):
        ref_offset = 0.0
        if len(self.references) > 0:
            ref_offset = self.references[0].state[0]

        if (self.bound_pos is not None
           and (self.target.state[0] > (ref_offset + self.bound_pos))):
            self.target.state[0] = (ref_offset + self.bound_pos)
        if (self.bound_neg is not None
           and (self.target.state[0] < (ref_offset + self.bound_neg))):
            self.target.state[0] = (ref_offset + self.bound_neg)


class SpringLawSolid(Constraint):

    def __init__(self, target, reference, spring_coeff, offset):
        self.spring_coeff = spring_coeff
        self.offset = offset
        super().__init__(target)
        self.references.append(reference)

    def apply(self):
        target = self.target.state[0]
        ref = self.references[0].state[0]

        penetration = (ref + self.offset) - target
        if np.sign(penetration) == np.sign(self.spring_coeff):
            force = (np.sign(self.spring_coeff)
                     * penetration
                     * self.spring_coeff)
            self.target.add_force(force)


class Condition:

    def __init__(self, target):
        self.target = target
        self.references = []

    def check(self, dt_s):
        return False


class ConditionOR(Condition):

    def __init__(self, references):
        super().__init__(None)

        if(isinstance(references, list)):
            for ref in references:
                self.references.append(ref)
        else:
            self.references.append(references)

    def check(self, dt_s):
        for ref in self.references:
            if(ref.check(dt_s)):
                return True
        return False


class ConditionAND(ConditionOR):

    def check(self, dt_s):
        for ref in self.references:
            if(not ref.check(dt_s)):
                return False
        return True


class PositionThreshold(Condition):

    def __init__(self, target, offset=0.0, check_greater=True, reference=None):
        super().__init__(target)
        if reference is not None:
            self.references.append(reference)
        self.check_greater = check_greater
        self.offset = offset

    def check(self, dt_s):
        ref_offset = 0.0
        if len(self.references) > 0:
            ref_offset = self.references[0].state[0]

        if self.check_greater:
            return (self.target.state[0] > (ref_offset + self.offset))
        else:
            return (self.target.state[0] < (ref_offset + self.offset))


class InRangeForDuration(Condition):

    def __init__(self,
                 target,
                 upper_bound,
                 lower_bound,
                 duration_s=1.0):

        super().__init__(target)

        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.duration_s = duration_s
        self.elapsed_s = 0.0

    def check(self, dt_s):
        if ((self.target.state[0] <= self.upper_bound)
           and (self.target.state[0] >= self.lower_bound)):
            self.elapsed_s += dt_s
        else:
            self.elapsed_s = 0.0
        return (self.elapsed_s >= self.duration_s)
