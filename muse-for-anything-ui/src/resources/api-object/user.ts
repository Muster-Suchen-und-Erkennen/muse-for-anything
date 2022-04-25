import { autoinject } from "aurelia-framework";
import { ApiLink, ApiObject, ApiResponse, matchesLinkRel } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { SchemaService } from "rest/schema-service";

@autoinject
export class User {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;
    skipNavigation: boolean = false;

    userRoles: ApiLink | null = null;

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

        const roles = modelData.apiResponse.links.find((link) => matchesLinkRel(link, ["collection", "user-role"]));
        // load resource from server to force cache refresh
        this.api.getByApiLink(roles, this.isRoot).then(() => {
            this.userRoles = roles; // only set link after cache was refreshed
        });

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
