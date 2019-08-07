from . import constants


def microalgos_to_algos(microalgos):
    """
    Convert microalgos to algos.

    Args:
        microalgos (int): how many microalgos

    Re turns:
        int or float: how many algos
    """
    return microalgos/constants.microalgos_to_algos_ratio


def algos_to_microalgos(algos):
    """
    Convert algos to microalgos.

    Args:
        algos (int or float): how many algos

    Returns:
        int: how many microalgos
    """
    return algos*constants.microalgos_to_algos_ratio
