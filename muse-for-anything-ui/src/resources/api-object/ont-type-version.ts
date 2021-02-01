import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiObject, ApiResponse } from "rest/api-objects";

@autoinject
export class OntTypeVersion {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean }) {
        this.apiObject = modelData.apiObject;
        this.isRoot = modelData.isRoot;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);
    }
}
