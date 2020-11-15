import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject } from "rest/api-objects";

@autoinject
export class Page {

    apiObject: ApiObject;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(apiObject: ApiObject) {
        console.log(apiObject);
        this.apiObject = apiObject;
    }
}
