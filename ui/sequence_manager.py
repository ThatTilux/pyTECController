from time import time


class SequenceManager:
    """
    Class for managing the state of a sequence.
    """

    def __init__(self, temperature_window):
        self.sequence = None
        self.finished = False
        self.paused = False
        # set temperature window
        self.temperature_window = temperature_window

    def set_sequence(self, sequence_values):
        """Sets a Sequence object.

        Args:
            sequence_values (list[(float, float, float, float)]): List of tuples with values for top_target, bottom_target, num_steps, time_sleep
        """
        self.sequence = Sequence(sequence_values, self.temperature_window)
        self.finished = False
        self.paused = False
        # when this is set to True, the next call of get_instructions will skip to the next step
        self.skip = False

    def get_instructions(self, top_temp, bottom_temp):
        """
        Returns new instructions or None when there are none.
        Format:
        ("target", (top_target, bottom_target))
        ("stop", None)
        """
        # if no sequence has been set or sequence is paused, return no instructions
        if not self.sequence or self.paused:
            return None

        # get new instructions
        new_top_target, new_bottom_target = self.sequence.get_new_targets(
            top_temp, bottom_temp, self.skip
        )

        if self.skip:
            self.skip = False

        # for None, there are no new instructions
        if new_top_target == None:
            return None

        # on -1, stop and clear the sequence
        if float(new_top_target) == -1.0:
            self.finished = True
            self.sequence = None
            return ("stop", None)

        # else, return the new targets
        return ("target", (new_top_target, new_bottom_target))

    def get_status(self):
        """
        Returns a string with the current status.
        """
        # check if sequence is finished
        if self.finished:
            return "Status: Sequence finished."

        # check for paused
        if self.paused:
            return "Status: Sequence paused."

        # if sequence has not been set yet
        if self.sequence is None:
            return "Status: Waiting for sequence."

        # get the current targets
        top, bottom, time = self.sequence.get_current_targets()

        top_range = (
            f"{top-self.temperature_window}°C to {top+self.temperature_window}°C"
        )
        bottom_range = (
            f"{bottom-self.temperature_window}°C to {bottom+self.temperature_window}°C"
        )

        # adjust status based on the time
        if time > 0:
            seconds = "second" if time == 1 else "seconds"
            status = f"Status: Waiting to hold a top temperature of {top_range} and a bottom temperature of {bottom_range} for {time} {seconds}."
        else:
            status = f"Status: Waiting to reach a top temperature of {top_range} and a bottom temperature of {bottom_range}."

        return status

    def delete_sequence(self):
        """
        Deletes the sequences.
        """
        self.sequence = None

    def set_paused(self, value):
        """
        Pauses / Unpauses the sequece. The sequence will not advance to the next step when it is paused.
        """
        assert type(value) is bool
        self.paused = value

    def skip_step(self):
        """
        The sequence will skip the current step.
        """
        self.skip = True


class Sequence:
    """
    Represents a sequence.
    """

    def __init__(self, sequence_values, temperature_window):
        """Creates a Sequence object.

        Args:
            sequence_values (list[(float, float, float, float)]): List of tuples with values for top_target, bottom_target, num_steps, time_sleep
        """
        # parse the sequence values to a list of SequenceElements
        self._parse_sequence(sequence_values, temperature_window)

    def _parse_sequence(self, sequence_values, temperature_window):
        """
        Creates a sequence based ob a list of sequence values.
        The first num_steps value must be 1.
        """
        sequence = []

        # assert that the first num_steps value is 1
        # this is caught in the ui so it should always be 1
        if len(sequence_values) > 0:
            assert sequence_values[0][2] == 1

        previous_target_top = -1
        previous_target_bottom = -1

        # parse each element
        for top_temp, bottom_temp, num_steps, time_sleep in sequence_values:
            # this is already caught in UI
            assert num_steps > 0

            # for num_steps == 1, add a sequence element
            if num_steps == 1:
                sequence.append(
                    SequenceElement(
                        top_temp, bottom_temp, time_sleep, temperature_window
                    )
                )
            # for num_steps > 1, create that many sequence elements
            else:
                # this temp has to be added in each element
                top_step = (top_temp - previous_target_top) / num_steps
                bottom_step = (bottom_temp - previous_target_bottom) / num_steps

                # add the sequence elements
                # we want to reach the new targets in num_steps steps
                for i in range(num_steps):
                    top_target = previous_target_top + top_step * (i + 1)
                    bottom_target = previous_target_bottom + bottom_step * (i + 1)
                    sequence.append(
                        SequenceElement(
                            top_target, bottom_target, time_sleep, temperature_window
                        )
                    )

            # set previous
            previous_target_top = top_temp
            previous_target_bottom = bottom_temp

        # save
        self.sequence = sequence

    def _get_current_sequence_element(self):
        if self.sequence:
            return self.sequence[0]
        return None

    def _next_sequence_element(self):
        """
        Moves on to the next sequence element.
        Returns the new first element or None when the sequence is finished.
        """
        if self.sequence:
            # remove first element
            self.sequence.pop(0)
            if self.sequence and self.sequence[0]:
                # reset time for that
                self.sequence[0].reset_time()
                # return it
                return self.sequence[0]
        return None

    def get_new_targets(self, top_temp, bottom_temp, skip=False):
        """
        Checks if the current sequence element is finished. If yes, move on to the next.
        Returns None or the new target temperatures or -1 when the sequence is finished.
        Format: top_target, bottom_target
        """
        # check if current is None
        if self._get_current_sequence_element() is None:
            # indicate the sequence is finished
            return -1, -1

        # check if the sequence element is finished or a skip was set
        if skip or self._get_current_sequence_element().is_finished(
            top_temp, bottom_temp
        ):
            # move on to the next element
            next = self._next_sequence_element()
            if next is None:
                # indicate the sequence is finished
                return -1, -1
            else:
                # return new targets
                return next.get_target_temps()
        # sequence element is not finished yet
        return None, None

    def get_current_targets(self):
        """
        Returns (top_target, bottom_target, time) for the current sequence element
        """
        current = self._get_current_sequence_element()
        top_temp, bottom_temp = current.get_target_temps()
        time = current.get_time()

        return (top_temp, bottom_temp, time)


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
            self.reset_time()
        return False

    def are_targets_reached(self, top_temp, bottom_temp):
        """
        Returns true if both target temperatures are reached (within the specified window).
        """
        # both temps have to be within the window
        if (
            top_temp >= self.top_target - self.TEMP_WINDOW
            and top_temp <= self.top_target + self.TEMP_WINDOW
            and bottom_temp >= self.bottom_target - self.TEMP_WINDOW
            and bottom_temp <= self.bottom_target + self.TEMP_WINDOW
        ):
            return True
        return False

    def get_target_temps(self):
        """
        Returns the target temperatures.
        Format: top_target, bottom_target
        """
        return self.top_target, self.bottom_target

    def get_time(self):
        """
        Returns the target time
        """
        return self.time_target

    def reset_time(self):
        self.time_unsuccess = time()
