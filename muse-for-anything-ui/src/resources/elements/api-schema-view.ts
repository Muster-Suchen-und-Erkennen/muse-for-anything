import { bindable, autoinject } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";

@autoinject
export class ApiSchemaView {
    @bindable data;
    @bindable schemaUrl;
    @bindable context: any;
    schema: NormalizedApiSchema;


    private schemaService: SchemaService;

    constructor(schemaService: SchemaService) {
        this.schemaService = schemaService;
    }

    schemaUrlChanged(newValue, oldValue) {
        const fragment = this.schemaService.getSchemaFragmentFromUrl(newValue);
        this.schemaService.getSchema(newValue)
            .then(schema => schema.getNormalizedApiSchema(fragment))
            .then(normalizedSchema => this.schema = normalizedSchema);
    }
}
