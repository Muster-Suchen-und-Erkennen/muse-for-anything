import { autoinject } from "aurelia-framework";
import { activationStrategy, RoutableComponentDetermineActivationStrategy } from 'aurelia-router';
import { BaseApiService } from "rest/base-api";

@autoinject
export class ExploreContent implements RoutableComponentDetermineActivationStrategy {
    path;
    apiLink;

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    determineActivationStrategy() {
        return activationStrategy.invokeLifecycle;
    }

    activate(routeParams: { path: string, [prop: string]: string }) {
        const basePath = routeParams.path;
        const queryParams = { ...routeParams };
        delete queryParams.path;
        const queryString = Object.keys(queryParams)
            .map(key => `${key}=${queryParams[key]}`)
            .join("&");
        this.path = `${basePath}?${queryString}`;
        this.api.resolveClientUrl(this.path).then(result => {
            this.apiLink = result;
        });
    }
}
