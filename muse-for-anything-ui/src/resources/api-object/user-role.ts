import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiObject, ApiResponse } from "rest/api-objects";

@autoinject
export class UserRole {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;
    skipNavigation: boolean = false;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean, skipNavigation: boolean }): void {
        this.apiObject = modelData.apiObject;
        this.isRoot = modelData.isRoot;
        this.skipNavigation = modelData.skipNavigation;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);
    }
}
