def get_following(sequence, current=0):
    """Get a next or previous item from a sequence in an infinite loop."""

    def following(seq):
        assert seq == 1 or seq == -1

        nonlocal current
        current += seq
        if current < 0:

            current = len(sequence) - 1
        if current == len(sequence):
            current = 0
        return current

    return following


class Context:
    """Context class which gets passed around across the various sidebars."""

    pass
