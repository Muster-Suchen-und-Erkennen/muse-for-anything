import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse } from "rest/api-objects";

@autoinject
export class OntObject {

    clientUrl: string;
    apiObject: ApiObject;
    isRoot: boolean = false;
    skipNavigation: boolean = false;

    latestVersionApiLink: ApiLink | null = null;
    allVersionsUrl: string | null = null;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(modelData: { apiObject: ApiObject, apiResponse: ApiResponse<unknown>, isRoot: boolean, skipNavigation: boolean }) {
        this.apiObject = modelData.apiObject;
        this.isRoot = modelData.isRoot;
        this.skipNavigation = modelData.skipNavigation;

        this.api.buildClientUrl(modelData.apiObject.self).then(url => this.clientUrl = url);

        this.latestVersionApiLink = modelData.apiResponse.links.find(link => {
            if (link.resourceType === "ont-object-version") {
                if (link.rel.some(rel => rel === "latest")) {
                    return true;
                }
            }
            return false;
        }) ?? null;

        const allVersionsLink = modelData.apiResponse.links.find(link => {
            if (link.resourceType === "ont-object-version") {
                if (link.rel.some(rel => rel === "collection")) {
                    return true;
                }
            }
            return false;
        }) ?? null;

        if (allVersionsLink) {
            this.api.buildClientUrl(allVersionsLink).then(url => this.allVersionsUrl = url);
        } else {
            this.allVersionsUrl = null;
        }
    }
}
