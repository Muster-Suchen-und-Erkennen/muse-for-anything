from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.taxonomies import Taxonomy
from muse_for_anything.db.models.ontology_objects import OntologyObject
from muse_for_anything.db.models.ontology_objects import OntologyObjectType

from jinja2 import Template, Environment, FileSystemLoader
import os

class OWL:

    def _map_namespace_to_owl(self, namespace: Namespace):
        # TODO implement mapping
        # for each attribute in namespace, create owl ontology namespace attribute
        # parse owl namespace in xml format
        # return owl namespace (in XML format)
        
        current_directory = os.getcwd()
        print("Current working directory:", current_directory)
        
        # Create a Jinja2 environment and specify the template folder
        env = Environment(loader=FileSystemLoader('/home/lizn/muse-for-anything/templates'))

        # Load the template from the file
        template = env.get_template('example.xml')

        # Define variables for name and description
        data = {
            'name': namespace.name,
            'description': namespace.description
            }

        # Render the template with the variables
        rendered_template = template.render(data)

        # Print or save the rendered template
        print(rendered_template)

        # You can save it to a file like this:
        # with open('output.html', 'w') as output_file:
        # output_file.write(rendered_template)


    def _map_taxonomy_to_owl(self, taxonomy: Taxonomy):
        # TODO implement mapping
        
        pass


    def _map_object_to_owl(self, object: OntologyObject):
        # TODO implement mapping

        
        pass


    def _map_type_tp_owl(self, type: OntologyObjectType):
        # TODO implement mapping
        
        pass

    