"""
All pydantic BaseModel class representations of Sandbox API responses
"""
from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

# added for dev intellisense: https://stackoverflow.com/a/71257588
if TYPE_CHECKING:
    from dataclasses import dataclass as _basemodel_decorator
else:
    def _basemodel_decorator(func):
        return func


class SandboxApiBaseModel(BaseModel):
    class Config:
        use_enum_values = True

    response_dict: dict = None
    """ the original dictionary received from api response """

    def pretty_json(self, indent=4, exclude_response=True):
        excluded_key_set = set()
        if exclude_response:
            excluded_key_set.add("response_dict")
        return self.json(indent=indent, exclude=excluded_key_set)


def list_to_model(response_list: List[dict], model: SandboxApiBaseModel) -> List[SandboxApiBaseModel]:
    return [dict_to_model(dict_item, model) for dict_item in response_list]


def dict_to_model(response_dict: dict, model: SandboxApiBaseModel) -> SandboxApiBaseModel:
    """ calls parse_obj, but additionally caches the response dict """
    wrapped_item = model.parse_obj(response_dict)
    wrapped_item.response_dict = response_dict
    return wrapped_item


class BlueprintAvailabilityStates(str, Enum):
    AVAILABLE = "Available Now"
    NOT_AVAILABLE = "Not Available"


class SandboxStates(str, Enum):
    PENDING = "Pending"
    BEFORE_SETUP = "BeforeSetup"
    PENDING_SETUP = "Pending Setup"
    RUNNING_SETUP = "Setup"
    READY = "Ready"
    ERROR = "Error"
    TEARDOWN = "Teardown"
    ENDED = "Ended"

    @classmethod
    def get_post_setup_states(cls) -> List:
        return [cls.READY, cls.ERROR, cls.TEARDOWN, cls.ENDED]

    @classmethod
    def get_active_states(cls) -> List:
        return [cls.READY, cls.ERROR]

    @classmethod
    def get_post_active_states(cls) -> List:
        return [cls.TEARDOWN, cls.ENDED]


class SetupStages(str, Enum):
    NONE = "None"
    PROVISIONING = "Provisioning"
    CONNECTIVITY = "Connectivity"
    CONFIGURATION = "Configuration"


class SandboxEventTypes(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class CommandParameterTypes(str, Enum):
    STRING = "String"
    NUMERIC = "Numeric"
    LOOKUP = "Lookup"


class CommandExecutionStates(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    STOPPING = "Stopping"
    CANCELLED = "Cancelled"
    COMPLETE = "Complete"
    FAILED = "Failed"


@_basemodel_decorator
class BlueprintInput(SandboxApiBaseModel):
    name: Optional[str]
    type: Optional[str]
    possible_values: Optional[List[str]]
    default_value: Optional[str]


@_basemodel_decorator
class BlueprintDescription(SandboxApiBaseModel):
    id: Optional[str]
    name: Optional[str]
    categories: Optional[List[str]]
    description: Optional[str]
    params: Optional[List[BlueprintInput]]
    availability: Optional[BlueprintAvailabilityStates]
    """ The availability of blueprint: ['Available Now', 'Not Available'] """
    estimated_setup_duration: Optional[str]
    """ Estimated blueprint setup duration. Uses'ISO 8601' Standard. (e.g 'PT23H' or 'PT4H2M') """


@_basemodel_decorator
class SandboxComponentBasic(SandboxApiBaseModel):
    id: Optional[str]
    name: Optional[str]
    type: Optional[str]
    component_type: Optional[str]
    description: Optional[str]
    address: Optional[str]
    app_lifecycle: Optional[str]


@_basemodel_decorator
class SandboxDetails(SandboxApiBaseModel):
    id: Optional[str]
    blueprint_id: Optional[str]
    type: Optional[str]
    name: Optional[str]
    permitted_users: Optional[List[str]]
    description: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    params: Optional[List[BlueprintInput]]
    components: Optional[List[SandboxComponentBasic]]
    state: Optional[SandboxStates]
    setup_stage: Optional[SetupStages]


@_basemodel_decorator
class BlueprintReference(SandboxApiBaseModel):
    id: Optional[str]
    name: Optional[str]


@_basemodel_decorator
class SandboxDescriptionShort(SandboxApiBaseModel):
    id: Optional[str]
    name: Optional[str]
    blueprint: Optional[BlueprintReference]
    description: Optional[str]
    state: Optional[SandboxStates]


@_basemodel_decorator
class SandboxEvent(SandboxApiBaseModel):
    id: Optional[int]
    event_type: Optional[SandboxEventTypes]
    event_text: Optional[str]
    output: Optional[str]
    time: Optional[str]
    """ Event time in 'ISO 8601' Standard. (e.g '2000-12-31T23:59:60Z') """


@_basemodel_decorator
class ActivityEventsResponse(SandboxApiBaseModel):
    num_returned_events: Optional[int]
    more_pages: Optional[bool]
    next_event_id: Optional[int]
    events: Optional[List[SandboxEvent]]


@_basemodel_decorator
class CommandParameterDetails(SandboxApiBaseModel):
    name: Optional[str]
    description: Optional[str]
    type: Optional[CommandParameterTypes]
    possibleValues: Optional[List[str]]
    defaultValue: Optional[str]
    mandatory: Optional[bool]


@_basemodel_decorator
class CommandParameterNameValue(SandboxApiBaseModel):
    name: Optional[str]
    value: Optional[str]


@_basemodel_decorator
class CommandExecution(SandboxApiBaseModel):
    id: Optional[str]
    status: Optional[CommandExecutionStates]
    supports_cancellation: Optional[bool]


@_basemodel_decorator
class Command(SandboxApiBaseModel):
    name: Optional[str]
    description: Optional[str]
    params: Optional[List[CommandParameterDetails]]
    executions: Optional[List[CommandExecution]]


@_basemodel_decorator
class CommandStartResponse(SandboxApiBaseModel):
    executionId: Optional[str]
    supports_cancellation: Optional[bool]


@_basemodel_decorator
class CommandContextDetails(SandboxApiBaseModel):
    sandbox_id: Optional[str]
    component_name: Optional[str]
    component_id: Optional[str]
    command_name: Optional[str]
    command_params: Optional[List[CommandParameterNameValue]]


@_basemodel_decorator
class CommandExecutionDetails(SandboxApiBaseModel):
    id: Optional[str]
    status: Optional[CommandExecutionStates]
    supports_cancellation: Optional[bool]
    started: Optional[str]
    ended: Optional[str]
    output: Optional[str]
    command_context: Optional[CommandContextDetails] = Field(description="additional data to populate about command. "
                                                                         "NOTE: this does not come from api response")


@_basemodel_decorator
class ComponentAttribute(SandboxApiBaseModel):
    type: Optional[str]
    name: Optional[str]
    value: Optional[str]


@_basemodel_decorator
class ConnectionInterface(SandboxApiBaseModel):
    name: Optional[str]
    url: Optional[str]


@_basemodel_decorator
class LinkMetadata(SandboxApiBaseModel):
    href: Optional[str]
    method: Optional[str]


@_basemodel_decorator
class SandboxComponentFull(SandboxApiBaseModel):
    id: Optional[str]
    name: Optional[str]
    type: Optional[str]
    component_type: Optional[str]
    description: Optional[str]
    address: Optional[str]
    app_lifecycle: Optional[str]
    attributes: Optional[List[ComponentAttribute]]
    connection_interfaces: Optional[List[ConnectionInterface]]
    _links: Optional[List[LinkMetadata]]


@_basemodel_decorator
class ExtendResponse(SandboxApiBaseModel):
    id: Optional[str]
    name: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    remaining_time: Optional[str]


@_basemodel_decorator
class SandboxOutputEntry(SandboxApiBaseModel):
    id: Optional[str]
    text: Optional[str]
    time: Optional[str]
    """ Event time in 'ISO 8601' Standard. (e.g '2000-12-31T23:59:60Z' """


@_basemodel_decorator
class SandboxOutput(SandboxApiBaseModel):
    number_of_returned_entries: Optional[int]
    next_entry_id: Optional[str]
    more_pages: Optional[bool]
    entries: Optional[List[SandboxOutputEntry]]


# Missing from Swagger Schema Docs
@_basemodel_decorator
class StopSandboxResponse(SandboxApiBaseModel):
    result: Optional[str] = "success"
