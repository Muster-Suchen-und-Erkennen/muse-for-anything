from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.taxonomies import Taxonomy
from muse_for_anything.db.models.ontology_objects import OntologyObject
from muse_for_anything.db.models.ontology_objects import OntologyObjectType

from jinja2 import Environment, FileSystemLoader
import os

class OWL:

    def _map_namespace_to_owl(self, namespace: Namespace, taxonomies: list[Taxonomy]):
        # TODO implement mapping
        # for each attribute in namespace, create owl ontology namespace attribute
        # parse owl namespace in xml format
        # return owl namespace (in XML format)
        
        current_directory = os.getcwd()
        print("Current working directory:", current_directory)
        
        env = Environment(loader=FileSystemLoader('muse_for_anything/templates'))

        template = env.get_template('example.xml')

        # taxonomy_item = {
        #     "name": "Item Name",
        #     "description": "Item Description"
        # }

        # taxonomies_test = []

        # for i in range(1, 4):
        #     taxonomy = {
        #         "name": f"Taxonomy {i}",
        #         "description": f"Description of Taxonomy {i}",
        #         "taxonomy_items": [taxonomy_item for _ in range(3)]
        #     }
        #     taxonomies_test.append(taxonomy)



        data = {
            'name': namespace.name,
            'description_of_the_namespace': namespace.description,
            'taxonomy_list': taxonomies
            }

        rendered_template = template.render(data)

        print(rendered_template)
    