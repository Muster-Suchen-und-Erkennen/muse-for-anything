from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.taxonomies import Taxonomy
from muse_for_anything.db.models.ontology_objects import OntologyObject
from muse_for_anything.db.models.ontology_objects import OntologyObjectType

from jinja2 import Environment, FileSystemLoader
import os

class OWL:

    def _map_namespace_to_owl(self, namespace: Namespace):
        # TODO implement mapping
        # for each attribute in namespace, create owl ontology namespace attribute
        # parse owl namespace in xml format
        # return owl namespace (in XML format)
        
        current_directory = os.getcwd()
        print("Current working directory:", current_directory)
        
        env = Environment(loader=FileSystemLoader('muse_for_anything/templates'))

        template = env.get_template('example.xml')

        data = {
            'name': namespace.name,
            'description_of_the_namespace': namespace.description
            }

        rendered_template = template.render(data)

        print(rendered_template)


    def _map_taxonomy_to_owl(self, taxonomy: Taxonomy):
        # TODO implement mapping
        
        pass


    def _map_object_to_owl(self, object: OntologyObject):
        # TODO implement mapping

        
        pass


    def _map_type_tp_owl(self, type: OntologyObjectType):
        # TODO implement mapping
        
        pass

    