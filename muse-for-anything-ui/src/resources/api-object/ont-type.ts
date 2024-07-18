import { autoinject } from "aurelia-framework";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";

@autoinject
export class OntType {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;
    skipNavigation: boolean = false;

    latestVersionApiLink: ApiLink | null = null;
    allVersionsUrl: string | null = null;

    schema: NormalizedApiSchema | null = null;
    schemaContext: any = {};

    private api: BaseApiService;
    private schemas: SchemaService;

    constructor(baseApi: BaseApiService, schemas: SchemaService) {
        this.api = baseApi;
        this.schemas = schemas;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean, skipNavigation: boolean }) {
        this.apiObject = modelData.apiObject;
        this.isRoot = modelData.isRoot;
        this.skipNavigation = modelData.skipNavigation;

        this.latestVersionApiLink = modelData.apiResponse.links.find(link => {
            if (link.resourceType === "ont-type-version") {
                if (link.rel.some(rel => rel === "latest")) {
                    return true;
                }
            }
            return false;
        }) ?? null;

        this.schemaContext = {
            baseApiLink: this.latestVersionApiLink,
        };

        const allVersionsLink = modelData.apiResponse.links.find(link => {
            if (link.resourceType === "ont-type-version") {
                if (link.rel.some(rel => rel === "collection")) {
                    return true;
                }
            }
            return false;
        }) ?? null;

        if (allVersionsLink) {
            this.api.buildClientUrl(allVersionsLink).then(url => this.allVersionsUrl = url);
        } else {
            this.allVersionsUrl = null;
        }

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);

        if (this.latestVersionApiLink) {
            this.schemas.getSchema(this.latestVersionApiLink.href)
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
