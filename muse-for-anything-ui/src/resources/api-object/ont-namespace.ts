import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";

@autoinject
export class OntNamespace {

    clientUrl: string;
    apiObject: ApiObject;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean }) {
        this.apiObject = modelData.apiObject;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);
    }
}
