import { autoinject, customElement } from "aurelia-framework";
import { ApiObject, ApiResponse } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";


@customElement("page-view")
@autoinject
export class Page {

    apiResponse: ApiResponse<unknown>;
    apiObject: ApiObject;

    skipNavigation: boolean = false;
    isObjectChooser: boolean = false;
    onObjectSelect = (object: any): void => {/* fallback */ };

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean, isObjectChooser: boolean, skipNavigation: boolean, onObjectSelect: (object: any) => void }) {
        this.skipNavigation = modelData.skipNavigation;
        this.isObjectChooser = modelData.isObjectChooser;
        this.onObjectSelect = modelData.onObjectSelect;
        this.apiObject = modelData.apiObject;
        this.apiResponse = modelData.apiResponse;
    }
}
