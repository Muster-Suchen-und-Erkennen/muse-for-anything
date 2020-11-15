import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";

@autoinject
export class Page {

    apiResponse: ApiResponse<unknown>;
    apiObject: ApiObject;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean }) {
        this.apiObject = modelData.apiObject;
        this.apiResponse = modelData.apiResponse;
    }
}
