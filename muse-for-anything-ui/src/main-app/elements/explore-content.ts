import { autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";

@autoinject
export class ExploreContent {
    path;
    apiLink;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    activate(routeParams: { path: string }) {
        this.path = routeParams.path;
        this.api.resolveClientUrl(this.path).then(result => this.apiLink = result);
    }

    valueChanged(newValue, oldValue) {
        //
    }
}
