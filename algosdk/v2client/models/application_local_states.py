# coding: utf-8


import pprint

class ApplicationLocalStates(object):
    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'id': 'int',
        'state': 'ApplicationLocalState'
    }

    attribute_map = {
        'id': 'id',
        'state': 'state'
    }

    def __init__(self, id=None, state=None):  # noqa: E501
        """ApplicationLocalStates - a model defined in OpenAPI"""  # noqa: E501

        self._id = None
        self._state = None

        self.id = id
        self.state = state

    @property
    def id(self):
        """Gets the id of this ApplicationLocalStates.  # noqa: E501


        :return: The id of this ApplicationLocalStates.  # noqa: E501
        :rtype: int
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this ApplicationLocalStates.


        :param id: The id of this ApplicationLocalStates.  # noqa: E501
        :type id: int
        """

        self._id = id

    @property
    def state(self):
        """Gets the state of this ApplicationLocalStates.  # noqa: E501


        :return: The state of this ApplicationLocalStates.  # noqa: E501
        :rtype: ApplicationLocalState
        """
        return self._state

    @state.setter
    def state(self, state):
        """Sets the state of this ApplicationLocalStates.


        :param state: The state of this ApplicationLocalStates.  # noqa: E501
        :type state: ApplicationLocalState
        """

        self._state = state

    def dictify(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, oas_attr in self.attribute_map.items():
            value = getattr(self, attr)
            if isinstance(value, list):
                result[oas_attr] = list(map(
                    lambda x: x.dictify() \
                    if hasattr(x, "dictify") else x,
                    value
                ))
            elif hasattr(value, "dictify"):
                result[oas_attr] = value.dictify()
            elif isinstance(value, dict):
                result[oas_attr] = dict(map(
                    lambda item: (item[0], item[1].dictify())
                    if hasattr(item[1], "dictify") else item,
                    value.items()
                ))
            else:
                result[oas_attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.dictify())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, ApplicationLocalStates):
            return False

        return self.dictify() == other.dictify()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, ApplicationLocalStates):
            return True

        return self.dictify() != other.dictify()
