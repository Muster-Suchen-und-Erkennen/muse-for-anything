import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";
import { SchemaService } from "rest/schema-service";

@autoinject
export class OntNamespace {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;
    skipNavigation: boolean = false;

    showGraph = false;

    private api: BaseApiService;
    private schemas: SchemaService;

    constructor(baseApi: BaseApiService, schemaService: SchemaService) {
        this.api = baseApi;
        this.schemas = schemaService;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean, skipNavigation: boolean }) {
        this.apiObject = modelData.apiObject;
        this.isRoot = modelData.isRoot;
        this.skipNavigation = modelData.skipNavigation;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);

        if (this.apiObject.self.schema != null && modelData.isRoot) {
            this.schemas.getSchema(this.apiObject.self.schema)
                .then(schema => schema.getNormalizedApiSchema())
                .then(schema => {
                    // console.log(schema);
                    // console.log(schema.normalized);
                    // console.log(schema.getPropertyList());
                });
        }
    }
}
