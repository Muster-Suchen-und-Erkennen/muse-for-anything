import { bindable, autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";

@autoinject
export class ApiResource {
    @bindable isRoot;
    @bindable apiLink;

    apiObject: ApiObject;
    modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean };
    objectType: string;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        this.objectType = null;
        this.apiObject = null;
        this.modelData = null;
        const ignoreCache = Boolean(this.isRoot);
        this.api.getByApiLink<ApiObject>(newValue, ignoreCache).then(apiResponse => {
            this.apiObject = apiResponse.data;
            this.modelData = {
                apiObject: apiResponse.data,
                apiResponse: apiResponse,
                isRoot: Boolean(this.isRoot),
            };
            const rels = apiResponse.data.self.rel;
            if (rels.some(rel => rel === "page")) {
                this.objectType = "page";
                return;
            }
            if (rels.some(rel => rel === "collection")) {
                this.objectType = "collection";
                return;
            }
            this.objectType = apiResponse.data.self.resourceType;
        });
    }
}
