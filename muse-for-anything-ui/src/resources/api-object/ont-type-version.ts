import { autoinject } from "aurelia-framework";
import { ApiObject, ApiResponse } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";

@autoinject
export class OntTypeVersion {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;

    schema: NormalizedApiSchema | null = null;

    private api: BaseApiService;
    private schemas: SchemaService;

    constructor(baseApi: BaseApiService, schemas: SchemaService) {
        this.api = baseApi;
        this.schemas = schemas;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean }) {
        this.apiObject = modelData.apiObject;
        this.isRoot = modelData.isRoot;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);

        if (this.apiObject != null) {
            this.schemas.getSchema(this.apiObject.self.href)
                .then(schema => schema.getNormalizedApiSchema())
                .then(schema => this.schema = schema);
        } else {
            this.schema = null;
        }
    }

    submit() {
        // dummy function, do nothing
    }
}
