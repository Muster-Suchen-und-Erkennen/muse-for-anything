import { bindable, autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";
import { NavigationLinksService } from "services/navigation-links";

@autoinject
export class ApiResource {
    @bindable isMain = false;
    @bindable isRoot;
    @bindable apiLink;

    apiObject: ApiObject;
    modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean };
    objectType: string;

    private api: BaseApiService;
    private navService: NavigationLinksService;

    constructor(baseApi: BaseApiService, navService: NavigationLinksService) {
        this.api = baseApi;
        this.navService = navService;
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        this.objectType = null;
        this.apiObject = null;
        this.modelData = null;
        const ignoreCache = Boolean(this.isRoot);
        const isMain = Boolean(this.isMain);
        this.api.getByApiLink<ApiObject>(newValue, ignoreCache).then(apiResponse => {
            this.apiObject = apiResponse.data;
            this.modelData = {
                apiObject: apiResponse.data,
                apiResponse: apiResponse,
                isRoot: Boolean(this.isRoot),
            };
            if (isMain) {
                this.navService.setMainApiResponse(apiResponse);
            }
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

    detached() {
        if (this.isMain) {
            this.navService.setMainApiResponse(null);
        }
    }
}
