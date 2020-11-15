import { bindable, autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject } from "rest/api-objects";

@autoinject
export class ApiResource {
    @bindable isRoot;
    @bindable apiLink;

    apiObject: ApiObject;
    objectType: string;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        const ignoreCache = Boolean(this.isRoot);
        this.api.get<ApiObject>(newValue, ignoreCache).then(apiResponse => {
            this.apiObject = apiResponse.data;
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
