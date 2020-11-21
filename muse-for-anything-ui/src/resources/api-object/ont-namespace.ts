import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";
import { SchemaService } from "rest/schema-service";

@autoinject
export class OntNamespace {

    clientUrl: string;
    apiObject: ApiObject;

    private api: BaseApiService;
    private schemas: SchemaService;

    constructor(baseApi: BaseApiService, schemaService: SchemaService) {
        this.api = baseApi;
        this.schemas = schemaService;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean }) {
        this.apiObject = modelData.apiObject;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);

        if (this.apiObject.self.schema != null) {
            this.schemas.getSchema(this.apiObject.self.schema).then(schema => schema.resolveSchema()).then(schema => console.log(schema));
        }
    }
}
