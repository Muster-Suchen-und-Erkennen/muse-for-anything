import { autoinject } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { activationStrategy, RoutableComponentDetermineActivationStrategy } from "aurelia-router";
import { NavigationLinksService, NavLinks } from "services/navigation-links";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject, ApiResponse, isApiObject } from "rest/api-objects";
import { NAV_LINKS_CHANNEL } from "resources/events";

@autoinject
export class CreateContent {

    createResourceType: string;
    createApiLink: ApiLink;
    context: any;

    private api: BaseApiService;
    private events: EventAggregator;
    private navService: NavigationLinksService;
    private subscription: Subscription;

    private path: string;
    private currentResponse: ApiResponse<ApiObject>;

    constructor(baseApi: BaseApiService, events: EventAggregator, navService: NavigationLinksService) {
        this.api = baseApi;
        this.events = events;
        this.navService = navService;
        this.subscribe();
    }

    subscribe(): void {
        this.subscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            if (true && navLinks.actions?.length > 0) {
                const actionLink = navLinks.actions.find(actionLink => {
                    if (actionLink.actionType !== "create") {
                        return false;
                    }
                    return actionLink.apiLink?.resourceType === this.createResourceType;
                });
                this.createApiLink = actionLink?.apiLink;
                this.context = {
                    action: "create",
                    actionLink: this.createApiLink,
                    baseApiLink: this.currentResponse?.data?.self,
                };
            } else {
                this.createApiLink = null;
            }
        });
    }

    detached() {
        this.subscription?.dispose();
    }

    determineActivationStrategy() {
        return activationStrategy.invokeLifecycle;
    }

    activate(routeParams: { path: string, resourceType: string, [prop: string]: string }) {
        this.createApiLink = null;
        const basePath = routeParams.path;
        this.createResourceType = routeParams.resourceType;
        const queryParams = { ...routeParams };
        delete queryParams.path;
        delete queryParams.resourceType;
        const queryString = Object.keys(queryParams)
            .map(key => `${key}=${queryParams[key]}`)
            .join("&");
        this.path = `${basePath}?${queryString}`;
        this.api.resolveClientUrl(this.path)
            .then(link => {
                return this.api.getByApiLink(link);
            })
            .then(response => {
                if (!isApiObject(response.data)) {
                    return; // TODO better error handling
                }
                this.currentResponse = response as ApiResponse<ApiObject>;
                this.navService.setMainApiResponse(this.currentResponse);
            });
    }

}
