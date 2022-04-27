"""
Component helpers for filtering and sorting the sandbox components
"""
from enum import Enum
from typing import List

from cloudshell.sandbox_rest import model
from cloudshell.sandbox_rest.api import SandboxRestApiSession


class ComponentTypes(str, Enum):
    app_type = "Application"
    resource_type = "Resource"
    service_type = "Service"


class AppLifeCycleTypes(str, Enum):
    deployed = "Deployed"
    un_deployed = "Undeployed"


class AttributeTypes(str, Enum):
    boolean = "boolean"
    password = "password"
    string = "string"
    numeric = "numeric"


class SandboxComponents:
    def __init__(self, components: List[model.SandboxComponentFull] = None):
        self.all_components = components or []

    def refresh_components(self, api: SandboxRestApiSession, sandbox_id: str) -> None:
        self.all_components = api.get_sandbox_components(sandbox_id)

    def _filter_components_by_type(self, component_type: ComponentTypes) -> List[model.SandboxComponentFull]:
        """ accepts both short info components and full info """
        return [component for component in self.all_components if component.component_type == component_type]

    def _filter_app_by_lifecycle(self, lifecycle_type: AppLifeCycleTypes) -> List[model.SandboxComponentFull]:
        return [component for component in self.all_components if component.component_type == ComponentTypes.app_type
                and component.app_lifecycle == lifecycle_type]

    @property
    def resources(self):
        return self._filter_components_by_type(ComponentTypes.service_type)

    @property
    def services(self):
        return self._filter_components_by_type(ComponentTypes.service_type)

    @property
    def deployed_apps(self):
        return self._filter_app_by_lifecycle(AppLifeCycleTypes.deployed)

    @property
    def un_deployed_apps(self):
        return self._filter_app_by_lifecycle(AppLifeCycleTypes.un_deployed)

    def filter_by_model(self, component_model: str) -> List[dict]:
        """
        Component Model / Shell Template
        ex: 'Juniper JunOS Switch Shell 2G'
        """
        return [component for component in self.all_components if component.component_type == component_model]

    def filter_by_attr(self, attr_name: str, attr_val: str) -> List[model.SandboxComponentFull]:
        """ attr name is shell agnostic, no namespacing """
        components = []
        for component in self.all_components:
            for attr in component.attributes:
                if attr.name.endswith(attr_name) and attr.value == attr_val:
                    components.append(component)
        return components

    def filter_by_boolean_attr(self, attr_name: str) -> List[dict]:
        """ attr name is shell agnostic, no namespacing """
        components = []
        for component in self.all_components:
            for attr in component.attributes:
                if attr.type == AttributeTypes.boolean and attr.name.endswith(attr_name) and attr.value == "True":
                    components.append(component)
        return components

