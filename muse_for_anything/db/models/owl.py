from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.taxonomies import Taxonomy, TaxonomyItem
from muse_for_anything.db.models.ontology_objects import OntologyObject
from muse_for_anything.db.models.ontology_objects import OntologyObjectType

from jinja2 import Environment, FileSystemLoader
import os

class OWL:

    def map_namespace_to_owl(self, namespace: Namespace):
        # TODO implement mapping
        # for each attribute in namespace, create owl ontology namespace attribute
        # parse owl namespace in xml format
        # return owl namespace (in XML format)
        
        taxonomies = Taxonomy.query.filter(
            Taxonomy.deleted_on == None,
            Taxonomy.namespace_id == namespace.id,
        ).all()
        
        ontology_object_types = OntologyObjectType.query.filter(
            OntologyObjectType.deleted_on == None,
            OntologyObjectType.namespace_id == namespace.id,
        ).all()
        
        ontology_objects = OntologyObject.query.filter(
            OntologyObject.deleted_on == None,
            OntologyObject.namespace_id == namespace.id,
        ).all()
        
        env = Environment(
            loader=FileSystemLoader('muse_for_anything/templates'),
            trim_blocks=True,
            lstrip_blocks=True)

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
            'taxonomy_list': taxonomies,
            'type_list': ontology_object_types,
            'object_list': [(object, self.get_ontology_object_variables(object)) for object in ontology_objects]
        }

        rendered_template = template.render(data)
        return rendered_template 

    def get_ontology_object_variables(self, ontology_object: OntologyObject):
        current = ontology_object.current_version
        data = current.data
        type = current.ontology_type_version
        root_schema = type.root_schema
        result = []
        if 'referenceType' in root_schema and 'referenceKey' in root_schema:
            ref_name = self.find_reference_name(data['referenceType'], data['referenceKey'])
            result.append({'name': ref_name, 'ref': ref_name})
        else:
            for name,value in data.items():
                property_schema = root_schema['properties'][name]
                if 'referenceType' in property_schema and 'referenceKey' in property_schema:
                    ref_name = self.find_reference_name(value['referenceType'], value['referenceKey'])
                    result.append({'name': name, 'ref': ref_name})
                else:
                    result.append({'name': name, 'value': value})
        return result
    
    def find_reference_name(self, reference_type, reference_key):
        if reference_type == 'ont-object':
            return OntologyObject.query.filter(
                OntologyObject.id == int(reference_key['objectId']),
            ).first().name
        elif reference_type == 'ont-taxonomy-item':
            return TaxonomyItem.query.filter(
                TaxonomyItem.id == int(reference_key['taxonomyItemId']),
            ).first().name
        else:
            raise Exception('Unknown reference type')  
    