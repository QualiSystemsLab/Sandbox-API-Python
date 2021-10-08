import json
from typing import List
from enum import Enum


class ComponentTypes(Enum):
    app_type = "Application"
    resource_type = "Resource"
    service_type = "Service"


class AppLifeCycleTypes(Enum):
    deployed = "Deployed"
    un_deployed = "Undeployed"


class AttributeTypes(Enum):
    boolean_type = "boolean"
    password_type = "password"
    string_type = "string"
    numeric_type = "numeric"


class SandboxRestComponents:
    def __init__(self, components: List[dict] = None):
        """
        if instantiated with components then populate lists
        if not, then call "refresh_components" after getting data from sandbox
         """
        self.all_components = components if components else []
        self.services = []
        self.resources = []
        self.deployed_apps = []
        self.un_deployed_apps = []
        if self.all_components:
            self._sort_components()

    def _filter_components_by_type(self, component_type: str) -> List[dict]:
        """ accepts both short info components and full info """
        return [component for component in self.all_components if component["type"] == component_type]

    def _filter_app_by_lifecycle(self, lifecycle_type):
        return [component for component in self.all_components
                if component["type"] == ComponentTypes.app_type.value
                and component["app_lifecyle"] == lifecycle_type]

    def _sort_components(self) -> None:
        """ sort stored components into separate lists """
        self.resources = self._filter_components_by_type(ComponentTypes.resource_type.value)
        self.services = self._filter_components_by_type(ComponentTypes.service_type.value)
        self.deployed_apps = self._filter_app_by_lifecycle(AppLifeCycleTypes.deployed.value)
        self.un_deployed_apps = self._filter_app_by_lifecycle(AppLifeCycleTypes.un_deployed.value)

    def refresh_components(self, components: List[dict]) -> None:
        self.all_components = components
        self._sort_components()

    def find_component_by_name(self, component_name: str) -> dict:
        for component in self.all_components:
            if component["name"] == component_name:
                return component

    @staticmethod
    def filter_by_model(components: List[dict], model: str) -> List[dict]:
        """
        Can pass in all components or sub list
        Both Resources and Applications can use same shell / model
        """
        return [component for component in components if component["component_type"] == model]

    def filter_by_attr_value(self, components: List[dict], attribute_name: str, attribute_value: str) -> List[dict]:
        """ attribute name does not have to include model / family namespace """
        self._validate_components_for_attributes(components)
        result = []
        for component in components:
            for attr in component["attributes"]:
                if attr["name"].endswith(attribute_name) and attr["value"] == attribute_value:
                    result.append(component)
        return result

    def filter_by_boolean_attr_true(self, components: List[dict], attribute_name: str) -> List[dict]:
        """ attribute name does not have to include model / family namespace """
        self._validate_components_for_attributes(components)
        result = []
        for component in components:
            for attr in component["attributes"]:
                if attr["name"].endswith(attribute_name) and attr["value"].lower() == "true":
                    result.append(component)
        return result

    @staticmethod
    def _validate_components_for_attributes(components: List[dict]):
        if not components:
            return
        attrs = components[0].get("attributes")
        if not attrs:
            raise Exception("'attributes' member not found. Must pass in Full info components.\n"
                            f"components data passed:\n{json.dumps(components, indent=4)}")
