from time import time


class SequenceManager:
    """
    Class for managing the state of the sequence.
    """

    def __init__(self):
        pass


class Sequence:
    """
    Represents a sequence.
    """
    def __init__(self):
        pass


class SequenceElement:
    """
    Represents one element of a sequence
    """

    def __init__(self, top_target, bottom_target, time_target, temperature_window):
        # target temperature of the top plate
        self.top_target = top_target
        # target temperature of the bottom plate
        self.bottom_target = bottom_target
        # targets have to be kept for this long to advance to the next step (in seconds)
        self.time_target = time_target
        # this is the most recent timestamp where the target temperature was not reached
        self.time_unsuccess = time()
        # target temperatures will count as reached when the temp is at the target +- this value
        self.TEMP_WINDOW = temperature_window
        

    def is_finished(self, top_temp, bottom_temp):
        """
        Checks if the element is finished. 
        Will return True if the targets are reached and the time_target has been met. 
        Will reset the start time if not.
        """
        # if the targets are reached, check the time
        # if they are not reached, reset the start time
        if self.are_targets_reached(top_temp, bottom_temp):
            # check if time target is reached
            if time() - self.time_unsuccess >= self.time_target:
                return True
        else:
            # reset unsuccess time
            self.time_unsuccess = time()
        return False

    def are_targets_reached(self, top_temp, bottom_temp):
        """
        Returns true if both target temperatures are reached (within the specified window).
        """
        # both temps have to be within the window
        if (
            top_temp >= self.top_target - self.TEMP_WINDOW
            and top_temp <= self.top_target + self.TEMP_WINDOW
            and bottom_temp >= self.top_target - self.TEMP_WINDOW
            and bottom_temp <= self.top_target + self.TEMP_WINDOW
        ):
            return True
        return False
